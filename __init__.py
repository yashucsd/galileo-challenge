from flask import Flask, render_template, request, make_response
from wtforms import Form, SubmitField, SelectField, validators
import requests, json

app = Flask(__name__)

# since this is a single page applicaiton, all routing is done thorugh the index
@app.route('/', methods=['GET', 'POST'])
def index():
	form = AddProvider(request.form)
	displayed = request.cookies.get('displayed') # cookie stores doctors that are already displayed
	docInfo = getDocInfo()

	if displayed: # translates info from cookie
		displayed = json.loads(displayed)

	# eliminates displayed doctors from choices to add
	updateChoices(form, displayed, docInfo)

	# handles the cases of a form submission (add/clear provider(s))
	if request.method == 'POST' and form.validate():
		if request.form['submit'] == 'Clear providers':
			displayed = None
		else:
			doctor = form.doctor.data

			if displayed:
				displayed[doctor] = True
			else:
				displayed = {doctor: True}

		# removes displayed doctor form choices
		updateChoices(form, displayed, docInfo)

	tasks = {}
	if displayed: # prepares the list of tasks for each doctor displayed
		updateTasks(tasks, displayed)

	response = make_response(render_template('doctors.html', form=form, displayed=displayed, tasks=tasks, docInfo=docInfo))
	response.set_cookie('displayed', json.dumps(displayed)) # stores the displayed doctors in a cookie

	return response

# stores doctor info from API into a dictionary accessible by doctor ID
def getDocInfo():
	data = json.loads(requests.get('https://testapi.io/api/akirayoglu/0/reference/getDoctors').text)
	docInfo = {}

	for doctor in data:
		docInfo[doctor['doctor_id']] = doctor

	return docInfo

# updates the doctors that can be added based on those displayed
def updateChoices(form, displayed, data):
	form.doctor.choices = []

	for d_id in data:
		if not displayed or (d_id not in displayed):
			doc = data[d_id]
			form.doctor.choices.append((d_id, " ".join([doc['first_name'], doc['last_name'], doc['degree']])))
			
	if len(form.doctor.choices) > 0:
		form.doctor.default = form.doctor.choices[0][0]

# prepares and sorts the list of tasks for each doctor accessible by doctor ID
def updateTasks(tasks, displayed):
	for doctor in displayed.keys():
		path = 'https://testapi.io/api/akirayoglu/0/tasks/' + doctor
		tasks[doctor] = json.loads(requests.get(path).text)
		if not tasks[doctor]:
			continue
		tasks[doctor].sort(key=lambda t: t['priority'], reverse=True)

# required class to handle buttons in view
class AddProvider(Form):
    doctor = SelectField('Doctor', validators=[validators.optional()])
    submit = SubmitField()