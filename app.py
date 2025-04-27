from flask import Flask, jsonify, request, render_template, redirect, url_for
import mysql.connector
import os
from datetime import datetime
import json

app = Flask(__name__)

# Database configuration
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'db'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'password'),
        database=os.environ.get('MYSQL_DATABASE', 'todos')
    )

# Initialize database if not exists
def init_db():
    conn = mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'db'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'password')
    )
    cursor = conn.cursor()
    
    # Create database if not exists
    cursor.execute("CREATE DATABASE IF NOT EXISTS todos")
    cursor.execute("USE todos")
    
    # Create todos table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task VARCHAR(255) NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM todos ORDER BY created_at DESC')
    todos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', todos=todos)

@app.route('/todos', methods=['GET'])
def get_todos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM todos ORDER BY created_at DESC')
    todos = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(todos)

@app.route('/todos', methods=['POST'])
def add_todo():
    task = request.form.get('task')
    if not task:
        return jsonify({'error': 'Task is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO todos (task) VALUES (%s)', (task,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if 'completed' in data:
        cursor.execute('UPDATE todos SET completed = %s WHERE id = %s', 
                       (data['completed'], todo_id))
    
    if 'task' in data:
        cursor.execute('UPDATE todos SET task = %s WHERE id = %s', 
                       (data['task'], todo_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM todos WHERE id = %s', (todo_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

# API endpoint to toggle todo status
@app.route('/todos/<int:todo_id>/toggle', methods=['POST'])
def toggle_todo(todo_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # First get current state
    cursor.execute('SELECT completed FROM todos WHERE id = %s', (todo_id,))
    todo = cursor.fetchone()
    
    if not todo:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Todo not found'}), 404
    
    # Toggle state
    new_state = not todo['completed']
    cursor.execute('UPDATE todos SET completed = %s WHERE id = %s', 
                   (new_state, todo_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
