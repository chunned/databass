
from databass import create_app

app = create_app()

if __name__ == "__main__":
    print('Launching databass......')
    app.run(
        host='0.0.0.0',
        port=8088,
        debug=True
    )
