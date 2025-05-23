from flask import Blueprint, render_template, jsonify, request
from app.llm import call_llm
from app.simulation import simulate_life
from app.visualization import visualize_life_meaning

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    return render_template('index.html')

@routes.route('/simulate')
def simulate():
    life_meaning = simulate_life()
    fig = visualize_life_meaning(life_meaning)
    plot_html = fig.to_html(full_html=False)
    return render_template('visualizations.html', plot_html=plot_html)

@routes.route('/llm', methods=['POST'])
def llm():
    prompt = request.json.get('prompt')
    response = call_llm(prompt)
    return jsonify({'response': response})
