import json
import os
from datetime import datetime, timedelta

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

# Load data from JSON files


def load_data():
    if os.path.exists('books.json'):
        with open('books.json', 'r') as f:
            books_data = json.load(f)
    else:
        books_data = []

    if os.path.exists('members.json'):
        with open('members.json', 'r') as f:
            members_data = json.load(f)
    else:
        members_data = []

    if os.path.exists('transactions.json'):
        with open('transactions.json', 'r') as f:
            transactions_data = json.load(f)
    else:
        transactions_data = []

    return books_data, members_data, transactions_data

# Save data to JSON files


def save_data(books_data, members_data, transactions_data):
    with open('books.json', 'w') as f:
        json.dump(books_data, f, indent=4)
    with open('members.json', 'w') as f:
        json.dump(members_data, f, indent=4)
    with open('transactions.json', 'w') as f:
        json.dump(transactions_data, f, indent=4)


# Home page
@app.route('/')
def index():
    books, members, _ = load_data()
    return render_template('index.html', books=books, members=members)


# Route for adding a book
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        data = request.form
        new_book = {
            'id': len(books) + 1,
            'title': data['title'],
            'author': data['author'],
            'genre': data['genre'],
            'publication_year': data['publication_year'],
            'stock_quantity': int(data['stock_quantity']),
            'rent_fee': float(data['rent_fee'])
        }

        books, members, transactions = load_data()
        books.append(new_book)
        save_data(books, members, transactions)

        return redirect(url_for('index'))

    return render_template('add_book.html')


# Route for adding a member
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        data = request.form
        new_member = {
            'id': len(members) + 1,
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'email': data['email'],
            'phone_number': data['phone_number'],
            'address': data['address'],
            'outstanding_debt': 0.0
        }

        books, members, transactions = load_data()
        members.append(new_member)
        save_data(books, members, transactions)

        return redirect(url_for('index'))

    return render_template('add_member.html')


# Route for issuing a book to a member
@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    books, members, transactions = load_data()

    if request.method == 'POST':
        data = request.form
        book_id = int(data['book_id'])
        member_id = int(data['member_id'])

        book = next((b for b in books if b['id'] == book_id), None)
        member = next((m for m in members if m['id'] == member_id), None)

        if not book or not member:
            return redirect(url_for('index'))

        if book['stock_quantity'] > 0 and member['outstanding_debt'] <= 500:
            book['stock_quantity'] -= 1

            # Calculate the due date (14 days from the transaction date)
            transaction_date = datetime.strptime(
                data['transaction_date'], '%Y-%m-%d')
            due_date = transaction_date + timedelta(days=14)

            # Calculate the number of days borrowed
            days_borrowed = (due_date - transaction_date).days

            # Calculate the rent fee
            rent_fee_per_day = book['rent_fee']
            rent_fee = rent_fee_per_day * days_borrowed

            # Add the transaction to the transactions list
            new_transaction = {
                "book_id": book_id,
                "member_id": member_id,
                "transaction_type": "issue",
                "transaction_date": data['transaction_date'],
                "due_date": due_date.strftime('%Y-%m-%d'),
                "days_borrowed": days_borrowed,
                "rent_fee": rent_fee
            }
            transactions.append(new_transaction)

            # Update outstanding debt for the member (if applicable)
            member['outstanding_debt'] += rent_fee

            save_data(books, members, transactions)

            return redirect(url_for('index'))

    return render_template('issue_book.html', books=books, members=members)

# Route for returning a book from a member


@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    books, members, transactions = load_data()

    if request.method == 'POST':
        data = request.form
        book_id = int(data['book_id'])
        member_id = int(data['member_id'])

        book = next((b for b in books if b['id'] == book_id), None)
        member = next((m for m in members if m['id'] == member_id), None)

        if not book or not member:
            return redirect(url_for('index'))

        # Calculate rent fee and update member's outstanding debt
        transaction_date = datetime.strptime(data['return_date'], '%Y-%m-%d')
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        days_borrowed = (transaction_date - due_date).days
        rent_fee = book['rent_fee'] * days_borrowed
        member['outstanding_debt'] += rent_fee

        book['stock_quantity'] += 1

        # Add the transaction to the transactions list
        new_transaction = {
            "book_id": book_id,
            "member_id": member_id,
            "transaction_type": "return",
            "transaction_date": data['return_date'],
            "due_date": data['due_date'],
            "rent_fee": rent_fee,
            "days_borrowed": days_borrowed
        }
        transactions.append(new_transaction)

        save_data(books, members, transactions)

        return redirect(url_for('index'))

    return render_template('return_book.html', books=books, members=members)


# Route for searching a book by name or author
@app.route('/search_book', methods=['GET', 'POST'])
def search_book():
    books, _, _ = load_data()

    if request.method == 'POST':
        data = request.form
        search_query = data['search_query'].lower()

        # Filter books that match the search query by title or author
        search_results = [b for b in books if search_query in b['title'].lower(
        ) or search_query in b['author'].lower()]

        return render_template('search_book.html', search_results=search_results)

    return render_template('search_book.html')


# Route for displaying the book inventory
@app.route('/book_inventory')
def book_inventory():
    books, _, _ = load_data()
    return render_template('book_inventory.html', books=books)


# Route for displaying the list of members
@app.route('/members')
def members():
    _, members, _ = load_data()
    return render_template('members.html', members=members)


# Route for displaying the list of transactions
@app.route('/transactions')
def transactions():
    _, _, transactions = load_data()
    return render_template('transactions.html', transactions=transactions)


if __name__ == '__main__':
    books, members, transactions = load_data()
    app.run(debug=True)
