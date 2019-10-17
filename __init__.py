from flask import Flask, render_template, request, make_response
from wtforms import Form, SubmitField, SelectField, validators
import requests, json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
	form = AddProvider(request.form)
	displayed = request.cookies.get('displayed') # the doctors that are already displayed
	docInfo = getDocInfo()

	if displayed:
		displayed = json.loads(displayed)

	updateChoices(form, displayed, docInfo)

	if request.method == 'POST' and form.validate():
		if request.form['submit'] == 'Clear providers':
			displayed = None
		else:
			doctor = form.doctor.data

			if displayed:
				displayed[doctor] = True
			else:
				displayed = {doctor: True}
		updateChoices(form, displayed, docInfo)

	tasks = {}
	if displayed:
		updateTasks(tasks, displayed)

	response = make_response(render_template('doctors.html', form=form, displayed=displayed, tasks=tasks, docInfo=docInfo))
	response.set_cookie('displayed', json.dumps(displayed))

	return response

def getDocInfo():
	data = json.loads(requests.get('https://testapi.io/api/akirayoglu/0/reference/getDoctors').text)
	docInfo = {}

	for doctor in data:
		docInfo[doctor['doctor_id']] = doctor

	return docInfo

def updateChoices(form, displayed, data):

	form.doctor.choices = []

	for d_id in data:
		if not displayed or (d_id not in displayed):
			doc = data[d_id]
			form.doctor.choices.append((d_id, " ".join([doc['first_name'], doc['last_name'], doc['degree']])))
			
	if len(form.doctor.choices) > 0:
		form.doctor.default = form.doctor.choices[0][0]

def updateTasks(tasks, displayed):
	for doctor in displayed.keys():
		path = 'https://testapi.io/api/akirayoglu/0/tasks/' + doctor
		tasks[doctor] = json.loads(requests.get(path).text)
		if not tasks[doctor]:
			continue
		tasks[doctor].sort(key=lambda t: t['priority'], reverse=True)

class AddProvider(Form):
    """Form to add provider to view."""

    doctor = SelectField('Doctor', validators=[validators.optional()])
    submit = SubmitField()