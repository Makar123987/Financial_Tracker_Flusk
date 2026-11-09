from required_modules import *
from services import available_categories, checked_category_id, current_balance, wrapped_site_case

app = Flask(__name__)
app.secret_key = environ["FLASK_SECRET_KEY"]

@app.route('/')
def home_page():
    """Show the home page."""
    return render_template('home_page.html')

@app.route('/login', methods=['GET', 'POST'])
def get_login():
    """Show the login form or sign in a user."""
    if request.method == 'GET':
        return render_template('login.html')
    else:
        init_db()
        password = request.form['password']
        email = request.form['email']
        data = db_session.execute(select(models.User).filter_by(email=email)).scalar_one_or_none()
        if data and check_password_hash(data.password, password):
            session['user_id'] = data.id
            return redirect('/category')
        else:
            return render_template(
                "error_template.html",
                error_title="Unable to log in",
                error_data="The email or password is incorrect. Please check your details and try again.",
                error_code=401,
                return_url="/login",
                return_label="Back to log in",
            ), 401

@app.route('/logout', methods=['GET'])
def log_out():
    """Sign out the current user."""
    session.clear()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def get_register():
    """Show the registration form or create a user."""
    if request.method == 'GET':
        return render_template('register.html')
    else:
        try:
            init_db()
            username = request.form['username']
            surname = request.form['surname']
            password = generate_password_hash(request.form['password'])
            email = request.form['email']
            user = models.User(name=username,surname=surname,password=password,email=email)
            db_session.add(user)
            db_session.commit()
            flash("Your account has been created successfully. You can now log in.", "registration_success")
            return redirect('/login')
        except exc.IntegrityError:
            db_session.rollback()
            return render_template(
                "error_template.html",
                error_title="Unable to create your account",
                error_data="An account with this email already exists. Use a different email or log in to your account.",
                error_code=409,
                return_url="/register",
                return_label="Back to registration",
            ), 409


@app.route('/category', methods=['GET', 'POST'])
@wrapped_site_case
def get_all_category():
    """List available categories or create a user category."""
    if request.method == 'GET':
        data = list(db_session.execute(select(models.Catgeory).filter_by(owner=session['user_id'])).scalars())
        data_system = list(db_session.execute(select(models.Catgeory).filter_by(owner=1)).scalars())
        return render_template("all_category.html", user_categories=data, system_categories=data_system)
    else:
        category_name = request.form['category_name']
        category_owner = session['user_id']
        new_category = models.Catgeory(name=category_name, owner=category_owner)
        db_session.add(new_category)
        db_session.commit()
        return redirect('/category')

@app.route('/category/<category_id>', methods=['GET', 'POST'])
@wrapped_site_case
def get_category(category_id):
    """Show or update a category and its transactions."""
    if 'user_id' in session:
        init_db()
        current_category = db_session.execute(select(models.Catgeory).filter_by(id=category_id)).scalars().first()
        if request.method == 'GET':
            transactions = list(db_session.execute(select(models.Transaction).filter_by(category=category_id,owner=session["user_id"])).scalars())
            return render_template('one_category.html', category=current_category, transactions=transactions)
        else:
            category_name = request.form["category_name"]
            if current_category.owner != 1:
                current_category.name = category_name
                db_session.commit()
            return redirect(f'/category/{category_id}')

    else:
        return redirect('/login')

@app.route('/category/<category_id>/delete', methods=['GET','POST'])
@wrapped_site_case
def delete_category(category_id):
    """Delete a category owned by the current user."""
    if 'user_id' in session:
        init_db()
        category = db_session.execute(
        select(models.Catgeory).filter_by(id=category_id, owner=session['user_id'])).scalars().first()
        db_session.delete(category)
        db_session.commit()
        return redirect("/category")
    else:
        return redirect("/login")


@app.route('/transactions', methods=['GET'])
@wrapped_site_case
def get_all_transactions():
    """Show the current user's transactions and financial summary."""
    categories = db_session.execute(select(models.Catgeory.id, models.Catgeory.name)
        .filter((models.Catgeory.owner == session['user_id']) | (models.Catgeory.owner == 1))).all()
    transactions = select(models.Transaction).filter_by(owner=session['user_id'])

    if "start_date" in request.args and "end_date" in request.args:
        date_from = datetime.strptime(request.args["start_date"], "%Y-%m-%d")
        date_to = datetime.strptime(request.args["end_date"], "%Y-%m-%d")
        transactions = select(models.Transaction).filter_by(owner=session['user_id']).filter(models.Transaction.date.between(date_from,date_to))

    transactions = list(db_session.execute(transactions).scalars())
    categories = {c.id : c.name for c in categories}

    aggregated_data = {"income": 0, "spend": 0}
    for tr in transactions:
        if tr.type == INCOME:
            aggregated_data["income"] += tr.amount
        else:
            aggregated_data["spend"] += tr.amount
    return render_template("dashboard.html", transactions=transactions, view_mode="all", aggregated_data=aggregated_data, category_names=categories, balance=current_balance())


@app.route('/transactions/<transaction_id>', methods=['GET', 'POST'])
@wrapped_site_case
def get_transaction(transaction_id):
    """Show or update a transaction owned by the current user."""
    if request.method == 'GET':
        transaction = db_session.execute(
            select(models.Transaction).filter_by(id=transaction_id, owner=session['user_id'])).scalars().first()
        return render_template("one_transaction.html", transaction=transaction, categories=available_categories())

    else:
        data = request.form
        tr = db_session.execute(
            select(models.Transaction).filter_by(owner=session['user_id'], id=transaction_id)
        ).scalar_one()

        tr.category = checked_category_id(data['transaction_category'])
        for field in ['description', 'amount', 'date', 'type']:
            setattr(tr, field, data[f"transaction_{field}"])
        db_session.commit()

        return redirect(f'/transactions/{transaction_id}')


@app.route('/transactions/<transaction_id>/delete', methods=['GET','POST'])
@wrapped_site_case
def delete_transaction(transaction_id):
    """Delete a transaction owned by the current user."""
    transaction = db_session.execute(
    select(models.Transaction).filter_by(id=transaction_id, owner=session['user_id'])).scalars().first()
    db_session.delete(transaction)
    db_session.commit()
    return redirect("/transactions")


@app.route('/income', methods=['GET', 'POST'])
@wrapped_site_case
def get_all_income():
    """List income transactions or add a new income transaction."""
    if request.method == 'GET':
        transactions = list(db_session.execute(select(models.Transaction).filter_by(owner=session['user_id'],type=INCOME)).scalars())
        categories = available_categories()
        return render_template("dashboard.html", transactions=transactions, view_mode='income', date=datetime.now(), categories=categories, category_names={c.id: c.name for c in categories}, balance=current_balance())
    else:
            transaction_description = request.form['description']
            transaction_category = checked_category_id(request.form['category'])
            transaction_amount = request.form['amount']
            transaction_date = request.form['date']
            transaction_owner = session['user_id']
            transaction_type = INCOME
            new_category = models.Transaction(description=transaction_description, category=transaction_category, amount=transaction_amount,date=transaction_date, owner=transaction_owner, type=transaction_type)
            db_session.add(new_category)
            db_session.commit()
            return redirect('/income')


@app.route('/spend', methods=['GET', 'POST'])
@wrapped_site_case
def get_all_spend():
    """List spending transactions or add a new spending transaction."""
    if request.method == 'GET':
        transactions = list(db_session.execute(select(models.Transaction).filter_by(owner=session['user_id'],type=SPEND)).scalars())
        categories = available_categories()
        return render_template("dashboard.html", transactions=transactions, view_mode='spend', date=datetime.now(), categories=categories, category_names={c.id: c.name for c in categories}, balance=current_balance())
    else:
            transaction_description = request.form['description']
            transaction_category = checked_category_id(request.form['category'])
            transaction_amount = request.form['amount']
            transaction_date = request.form['date']
            transaction_owner = session['user_id']
            transaction_type = SPEND
            new_category = models.Transaction(description=transaction_description, category=transaction_category, amount=transaction_amount,date=transaction_date, owner=transaction_owner, type=transaction_type)
            db_session.add(new_category)
            db_session.commit()
            return redirect('/spend')


if __name__ == '__main__':
    app.run()
