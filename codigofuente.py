from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from celery import Celery

app = Flask(__name__)

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'tucorreo@gmail.com'  
app.config['MAIL_PASSWORD'] = 'tucontraseña'  # 
app.config['MAIL_DEFAULT_SENDER'] = 'tucorreo@gmail.com' 
app.secret_key = 'supersecretkey'  

# celery aca
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',  # Usamos Redis como broker
    CELERY_RESULT_BACKEND='redis://localhost:6379/0',  # Redis para almacenar resultados
)

celery = make_celery(app)
mail = Mail(app)

# Lista de recetas 
recetas = []


@app.route("/")
def index():
    return render_template("index.html", recetas=recetas)


@app.route("/nueva", methods=["GET", "POST"])
def nueva_receta():
    if request.method == "POST":
        titulo = request.form["titulo"]
        ingredientes = request.form["ingredientes"]
        instrucciones = request.form["instrucciones"]

        # Guardar receta
        recetas.append({
            "titulo": titulo,
            "ingredientes": ingredientes,
            "instrucciones": instrucciones
        })

        # Enviar correo después de agregar receta
        destinatario = request.form["correo"] 
        send_email_async(destinatario, titulo)

        flash('Receta creada con éxito y correo enviado.', 'success')
        return redirect(url_for("index"))
    return render_template("nueva_receta.html")


# Tarea asíncrona para enviar correo
@celery.task
def send_email_async(destinatario, titulo_receta):
    try:
        msg = Message('Receta Nueva Creada', recipients=[destinatario])
        msg.body = f"Se ha creado una nueva receta: {titulo_receta}. ¡Disfrútala!"
        mail.send(msg)
    except Exception as e:
        print(f"Error enviando correo: {e}")
        flash("Hubo un error al intentar enviar el correo. Inténtalo nuevamente.", "error")


if __name__ == "__main__":
    app.run(debug=True)
