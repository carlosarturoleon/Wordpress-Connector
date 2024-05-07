from flask import Flask
from routes import configure_routes


app = Flask(__name__)


configure_routes(app)


# Run the flask app to obtain the code
if __name__ == '__main__':
    app.run()