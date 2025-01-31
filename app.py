from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource, reqparse
from models import db, Article, SuggestedArticle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nfcco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Suggested Article Resource
class SuggestedArticleResource(Resource):
    def get(self):
        suggestions = SuggestedArticle.query.all()
        return [
            {
                "id": suggestion.id,
                "title": suggestion.title,
                "content": suggestion.content,
                "author_name": suggestion.author_name,
                "image_url": suggestion.image_url,
                "suggested_at": suggestion.suggested_at.strftime('%Y-%m-%d %H:%M:%S')
            } for suggestion in suggestions
        ]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True, help="Title cannot be blank")
        parser.add_argument('content', required=True, help="Content cannot be blank")
        parser.add_argument('author_name', required=True, help="Author name cannot be blank")
        parser.add_argument('image_url', required=False)
        parser.add_argument('category', required=False)
        data = parser.parse_args()

        new_suggestion = SuggestedArticle(
            title=data['title'],
            content=data['content'],
            author_name=data['author_name'],
            image_url=data.get('image_url'),
        )
        db.session.add(new_suggestion)
        db.session.commit()
        return {"message": "Suggested article submitted successfully"}, 201


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
                image_url=suggestion.image_url,  # Ensure this field is passed correctly
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

from flask_restful import Resource
from models import Article

class ApprovedArticlesResource(Resource):
    def get(self):
        # Query the database for articles where approved is True
        approved_articles = Article.query.filter_by(approved=True).all()
        
        # Convert the articles to a list of dictionaries
        articles_list = [
            {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'author_name': article.author_name,
                'image_url': article.image_url,
                'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
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
