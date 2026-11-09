from required_modules import models, session, abort, db_session, select, INCOME, SPEND, init_db, redirect
from functools import wraps

def available_categories():
    """Return the system categories and the current user's categories."""
    return list(db_session.execute(select(models.Catgeory).filter(
        (models.Catgeory.owner == session['user_id']) | (models.Catgeory.owner == 1)
    ).order_by(models.Catgeory.name)).scalars())

def checked_category_id(value):
    """Return a category ID only if the current user can use it."""
    category_id = int(value) if value.isdigit() else None
    if category_id not in {category.id for category in available_categories()}:
        abort(400, description='Please choose an available category.')
    return category_id

def current_balance():
    """Calculate the current user's income minus spending."""
    transactions = db_session.execute(select(models.Transaction.amount, models.Transaction.type)
                                      .filter_by(owner=session['user_id'])).all()
    return sum((amount or 0) * (1 if kind == INCOME else -1) for amount, kind in transactions)

def wrapped_site_case(func):
    """Wrap the site case."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' in session:
            init_db()
            return func(*args, **kwargs)
        else:
            return redirect('/login')
    return wrapper



