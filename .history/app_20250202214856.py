import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, Article, SuggestedArticle
import base64  # For encoding image data to base64


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nfcco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/uploads/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size 16MB

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)
CORS(app, origins=["http://localhost:5173","https://nffco-backend.onrender.com"])  # Allow requests from the React app

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Utility function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class SuggestedArticleResource(Resource):
    def post(self):
        image_data = None  # Initialize image_data

        if 'image_url' in request.files:
            file = request.files['image_url']
            if file and allowed_file(file.filename):
                try:
                    image_data = file.read()  # Read the file data as bytes
                except Exception as e:
                    print(f"Error reading image file: {e}")
                    return {"message": "Error processing image"}, 500
            else:
                return {"message": "Invalid image format"}, 400

        title = request.form.get('title')
        content = request.form.get('content')
        author_name = request.form.get('author_name')

        if not title or not content or not author_name:
            return {"message": "Title, content, and author_name are required"}, 400

        new_suggestion = SuggestedArticle(
            title=title,
            content=content,
            author_name=author_name,
            image_data=image_data,  # Store the image data
        )

        try:
            db.session.add(new_suggestion)
            db.session.commit()
            return {"message": "Suggested article submitted successfully"}, 201
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return {"message": "An error occurred while submitting the article"}, 500

    def get(self):
        suggested_articles = SuggestedArticle.query.all()
        articles_list = []
        for article in suggested_articles:
            image_base64 = None
            if article.image_data:
                image_base64 = base64.b64encode(article.image_data).decode('utf-8')

            articles_list.append({
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'author_name': article.author_name,
                'image_data': image_base64,  # Send base64 encoded image data
            })
        return {'suggested_articles': articles_list}, 200
    
    

# Admin Approval Resource
class AdminApprovalResource(Resource):
    def post(self, suggestion_id):
        parser = reqparse.RequestParser()
        parser.add_argument('action', required=True, choices=('approve', 'reject'), help="Action must be 'approve' or 'reject'")
        data = parser.parse_args()

        suggestion = SuggestedArticle.query.get_or_404(suggestion_id)

        if data['action'] == 'approve':
            # Create a new Article from the suggested article
            new_article = Article(
                title=suggestion.title,
                content=suggestion.content,
                author_name=suggestion.author_name,
                image_data=suggestion.image_data,  # Ensure this field is passed correctly
                approved=True  # Set approved to True
            )
            db.session.add(new_article)
            db.session.delete(suggestion)  # Remove from suggested articles
            db.session.commit()
            return {"message": "Article approved and published"}, 201

        elif data['action'] == 'reject':
            db.session.delete(suggestion)  # Just delete the suggestion if rejected
            db.session.commit()
            return {"message": "Article suggestion rejected"}, 200

# Approved Articles Resource

class ApprovedArticlesResource(Resource):
    def get(self):
        approved_articles = Article.query.filter_by(approved=True).all()

        articles_list = [
            {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'author_name': article.author_name,
                'image_data': base64.b64encode(article.image_data).decode('utf-8') if article.image_data else None,
                'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'approved': article.approved
            }
            for article in approved_articles
        ]

        return {'approved_articles': articles_list}, 200

# Register Resources
api.add_resource(SuggestedArticleResource, '/suggested_articles')
api.add_resource(AdminApprovalResource, '/admin/approval/<int:suggestion_id>')
api.add_resource(ApprovedArticlesResource, '/articles/approved')

if __name__ == '__main__':
    app.run(debug=True)
