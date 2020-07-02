import json
import falcon


def post_healthcheck(self, data):
    try:
        with open("/tmp/dclient-healthcheck.json", "w") as file:
            file.write(json.dumps(data))
        response_object = {
            "body": {
                "status": "success",
                "message": "New healthcheck successfully created.",
                "data": data
            },
            "status": falcon.HTTP_201
        }
        return response_object
    except:
        response_object = {
            "body": {
                "status": "fail",
                "message": "POST healthcheck failed.",
            },
            "status": falcon.HTTP_409
        }
        return response_object


def get_healthcheck(self):
    response_object = {
        'body': {
            'status': 'success',
            'message': 'system is healthy'
        },
        'status': falcon.HTTP_200
    }
    return response_object
