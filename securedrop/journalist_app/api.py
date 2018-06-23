from functools import wraps
import json

from flask import abort, Blueprint, jsonify, request

import config
from db import db
from journalist_app import utils
from models import Journalist, Source, Submission


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
        except:
            return abort(403, 'API token not found in Authorization header.')

        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        if not Journalist.verify_api_token(auth_token):
            return abort(403, 'API token is invalid or expired.')
        return f(*args, **kwargs)
    return decorated_function


def get_or_404(model, object_id):
    result = model.query.get(object_id)
    if result is None:
        abort(404)
    return result


def make_blueprint(config):
    api = Blueprint('api', __name__)

    @api.route('/')
    def get_endpoints():
        endpoints = {'sources_url': '/api/v1/sources/',
                     'current_user_url': '/api/v1/user/',
                     'submissions_url': '/api/v1/submissions/',
                     'auth_token_url': '/api/v1/token/'}
        return jsonify(endpoints), 200

    @api.route('/token/', methods=['POST'])
    def get_token():
        creds = json.loads(request.data)
        username = creds['username']
        password = creds['password']
        one_time_code = creds['one_time_code']
        try:
            journalist = Journalist.login(username, password, one_time_code)
            return jsonify({'token': journalist.generate_api_token(
                 expiration=1800), 'expiration': 1800}), 200
        except:
            return abort(403, 'Token authentication failed.')

    @api.route('/sources/', methods=['GET'])
    @token_required
    def get_all_sources():
        sources = Source.query.all()
        return jsonify(
            {'sources': [source.to_json() for source in sources]}), 200

    @api.route('/sources/<int:source_id>/', methods=['GET'])
    @token_required
    def single_source(source_id):
        source = get_or_404(Source, source_id)
        return jsonify(source.to_json()), 200

    @api.route('/sources/<int:source_id>/add_star/', methods=['POST'])
    @token_required
    def add_star(source_id):
        source = get_or_404(Source, source_id)
        utils.make_star_true(source.filesystem_id)
        db.session.commit()
        return jsonify({'message': 'Star added'}), 201

    @api.route('/sources/<int:source_id>/remove_star/', methods=['DELETE'])
    @token_required
    def remove_star(source_id):
        source = get_or_404(Source, source_id)
        utils.make_star_false(source.filesystem_id)
        db.session.commit()
        return jsonify({'message': 'Star removed'}), 200

    @api.route('/sources/<int:source_id>/submissions/', methods=['GET',
                                                                 'DELETE'])
    @token_required
    def all_source_submissions(source_id):
        pass

    @api.route('/sources/<int:source_id>/submissions/<int:submission_id>/download/',  # noqa
               methods=['GET'])
    @token_required
    def download_submission(source_id, submission_id):
        pass

    @api.route('/sources/<int:source_id>/submissions/<int:submission_id>/',
               methods=['GET', 'DELETE'])
    @token_required
    def single_submission(source_id, submission_id):
        pass

    @api.route('/sources/<int:source_id>/reply/', methods=['POST'])
    @token_required
    def post_reply(source_id):
        pass

    @api.route('/submissions/', methods=['GET'])
    @token_required
    def get_all_submissions():
        submissions = Submission.query.all()
        return jsonify({'submissions': [submission.to_json() for \
                                        submission in submissions]}), 200

    return api
