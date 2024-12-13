from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import os

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'default_fallback_key')

# Database configuration
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345678',
        database='fortune21'
    )
    return conn

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    ref_by = request.args.get('ref_by', '')  # Get the referral code from the URL parameters

    if request.method == 'POST':
        try:
            username = request.form['username']
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form['phone']
            password = request.form['password']
            country = request.form['country']
            ref_by = request.form.get('ref_by', None)  # Optional field

            print(f"Received data: username={username}, full_name={full_name}, email={email}, phone={phone}, password={password}, country={country}, ref_by={ref_by}")

            # Connect to the database
            conn = get_db_connection()
            if conn is None:
                flash('Database connection error. Please try again later.', 'danger')
                return redirect(url_for('register'))
            cursor = conn.cursor()

            # Check if the email already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Email already registered!', 'danger')
                return redirect(url_for('register'))

            # Insert the new user into the database with an initial balance of 5.00
            cursor.execute("""
                           INSERT INTO users (username, full_name, email, phone, password, country, ref_by, balance)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                           """, (username, full_name, email, phone, password, country, ref_by, 5.00))
            conn.commit()  # Save the changes
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except KeyError as e:
            flash(f'Missing form field: {e}', 'danger')
        except Exception as e:
            flash('There was an issue with your registration. Please try again later.', 'danger')
            print(f"An error occurred: {e}")
            if conn:
                conn.rollback()  # Rollback in case of error
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('register.html', ref_by=ref_by)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn is None:
            flash('Database connection error. Please try again later.', 'danger')
            return redirect(url_for('login'))
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            # Set session variables
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['full_name'] = user[2]
            session['email'] = user[3]
            session['theme'] = user[4]  # Assuming user[4] is the theme
            return redirect(url_for('dashboard'))  # Redirect to the dashboard
        else:
            flash('Invalid email or password!', 'danger')

        cursor.close()
        conn.close()

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to login first.', 'success')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch the user's data from the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT u.username, u.full_name, u.theme, u.balance,
           COALESCE(t.total_profit, 0) AS total_profit, 
           COALESCE(t.total_bonus, 0) AS total_bonus, 
           COALESCE(t.referral_bonus, 0) AS referral_bonus, 
           COALESCE(t.total_deposit, 0) AS total_deposit, 
           COALESCE(t.total_withdrawal, 0) AS total_withdrawal,
           COALESCE(t.total_investments, 0) AS total_investments,
           COALESCE(t.active_investments, 0) AS active_investments
    FROM users u
    LEFT JOIN transactions t ON u.id = t.user_id
    WHERE u.id = %s
    """
    cursor.execute(query, (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        username = user_data['username']
        full_name = user_data['full_name']
        theme = user_data['theme']
        balance = user_data['balance']
        total_profit = user_data['total_profit']
        total_bonus = user_data['total_bonus']
        referral_bonus = user_data['referral_bonus']
        total_deposit = user_data['total_deposit']
        total_withdrawal = user_data['total_withdrawal']
        total_investments = user_data['total_investments']
        active_investments = user_data['active_investments']
        account_balance = balance  # Use the balance directly
    else:
        username = 'Unknown User'
        full_name = 'No Name Available'
        theme = 'light'
        balance = 0.00
        total_profit = 0.00
        total_bonus = 0.00
        referral_bonus = 0.00
        total_deposit = 0.00
        total_withdrawal = 0.00
        total_investments = 0
        active_investments = 0
        account_balance = 0.00

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        username=username,
        full_name=full_name,
        theme=theme,
        balance=balance,
        total_profit=total_profit,
        total_bonus=total_bonus,
        referral_bonus=referral_bonus,
        total_deposit=total_deposit,
        total_withdrawal=total_withdrawal,
        total_investments=total_investments,
        active_investments=active_investments,
        account_balance=account_balance,
        user_data=user_data,
        
    )

@app.route('/change_theme', methods=['POST'])
def change_theme():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    new_theme = request.form.get('theme')

    if new_theme not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET theme = %s WHERE id = %s", (new_theme, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    session['theme'] = new_theme

    return jsonify({'success': 'Theme updated'}), 200


@app.route('/about')
def about():
    username = session.get('email')  

    full_name = session.get('full_name') 
    return render_template('about.html', username=username, full_name=full_name)


@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        amount = request.form.get('amount')
        paymethod = request.form.get('paymethod')

        # Validate the amount
        if float(amount) < 200:
            flash('The minimum deposit amount is 200.')
            return redirect(url_for('deposits'))

        # Validate the payment method
        if not paymethod:
            flash('No payment method chosen.')
            return redirect(url_for('deposits'))

        # Define the addresses for each payment method
        addresses = {
            'Ethereum': '0xa1c0b1f693b67d411615987ab2a9a4230995d66b',
            'Bitcoin': '3PgMT6rPDwf1NiFTFdgD5Dqj2jGsm4jBfc',
            'Solana': 'EGnp4F9piVCksy8iEgF1MptgiFreis5CwDD5j3wnijtt',
            'USDT': 'UQCx4wjVOj-_JmiGp0FyBT8Dn0AnVqj9IwwiNbk606SRMK2Q',
            'Litecoin': 'LcAFxihBDriSC8nv8myaHzYLvjc6hnBe7e'
        }

        address = addresses.get(paymethod, 'Unknown Address')

        username = session.get('email')
        full_name = session.get('full_name')
        return render_template('payment.html', username=username, full_name=full_name, amount=amount, paymethod=paymethod, address=address)
    else:
        return redirect(url_for('deposits'))
    
@app.route('/terms')
def terms():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('terms.html', username=username, full_name=full_name)

@app.route('/trading_strategies')
def trading_strategies():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('trading_strategies.html', username=username, full_name=full_name)

@app.route('/risk_disclosure')
def risk_disclosure():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('risk_disclosure.html', username=username, full_name=full_name)

@app.route('/privacy_policy')
def privacy_policy():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('privacy_policy.html', username=username, full_name=full_name)

@app.route('/customer_agreement')
def customer_agreement():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('customer_agreement.html', username=username, full_name=full_name)

@app.route('/aml_policy')
def aml_policy():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('aml_policy.html', username=username, full_name=full_name)

@app.route('/google_login')
def google_login():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('google_login.html', username=username, full_name=full_name)

@app.route('/forgot_password')
def forgot_password():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('forgot_password.html', username=username, full_name=full_name)

@app.route('/auth_google_redirect')
def auth_google_redirect():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('auth_google_redirect.html', username=username, full_name=full_name)

@app.route('/markets')
def markets():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('markets.html', username=username, full_name=full_name)

@app.route('/contact')
def contact():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('contact.html', username=username, full_name=full_name)

@app.route('/education')
def education():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('education.html', username=username, full_name=full_name)

@app.route('/confirm-password')
def confirm_password():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('confirm-password.html', username=username, full_name=full_name)

@app.route('/deposits', methods=['GET', 'POST'])
def deposits():
    if 'user_id' not in session:
        flash('You need to login first.', 'success')
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = request.form['amount']
        paymethod = request.form['paymethod']

        if not paymethod:
            flash('Please choose a payment method by clicking on it', 'danger')
            return redirect(url_for('deposits'))

        if float(amount) < 200:
            flash('The minimum deposit amount is 200.', 'danger')
            return redirect(url_for('deposits'))

        # Process the deposit (e.g., save to database, initiate payment, etc.)
        # ...

        flash('Deposit successful!', 'success')
        return redirect(url_for('dashboard'))

    user_id = session['user_id']

    # Fetch the user's data from the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT u.username, u.full_name, u.email, u.theme, u.balance,
           COALESCE(t.total_profit, 0) AS total_profit, 
           COALESCE(t.total_bonus, 0) AS total_bonus, 
           COALESCE(t.referral_bonus, 0) AS referral_bonus, 
           COALESCE(t.total_deposit, 0) AS total_deposit, 
           COALESCE(t.total_withdrawal, 0) AS total_withdrawal,
           COALESCE(t.total_investments, 0) AS total_investments,
           COALESCE(t.active_investments, 0) AS active_investments
    FROM users u
    LEFT JOIN transactions t ON u.id = t.user_id
    WHERE u.id = %s
    """
    cursor.execute(query, (user_id,))
    user_data = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('deposits.html', user_data=user_data)

@app.route('/support')
def support():
    if 'user_id' not in session:
        flash('You need to login first.', 'success')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch the user's data from the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT u.username, u.full_name, u.email, u.theme, u.balance,
           COALESCE(t.total_profit, 0) AS total_profit, 
           COALESCE(t.total_bonus, 0) AS total_bonus, 
           COALESCE(t.referral_bonus, 0) AS referral_bonus, 
           COALESCE(t.total_deposit, 0) AS total_deposit, 
           COALESCE(t.total_withdrawal, 0) AS total_withdrawal,
           COALESCE(t.total_investments, 0) AS total_investments,
           COALESCE(t.active_investments, 0) AS active_investments
    FROM users u
    LEFT JOIN transactions t ON u.id = t.user_id
    WHERE u.id = %s
    """
    cursor.execute(query, (user_id,))
    user_data = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('support.html', user_data=user_data)

@app.route('/withdrawals')
def withdrawals():
    username = session.get('email')
    full_name = session.get('full_name')
    return render_template('withdrawals.html', username=username, full_name=full_name)
    



@app.route('/trading_history')
def trading_history():
    username = session.get('email')  
    email = session.get('username')
    full_name = session.get('full_name') 
    return render_template('trading_history.html', username=username, full_name=full_name, email = email)

@app.route('/account_settings')
def account_settings():
    email = session.get('username')
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('account_settings.html', username=username, full_name=full_name, email = email)

@app.route('/buy-plan', methods=['GET'])
def buy_plan():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('buy-plan.html', username=username, full_name=full_name)

@app.route('/asset-balance')
def asset_balance():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('asset-balance.html', username=username, full_name=full_name)

@app.route('/manage-account-security')
def manage_account_security():
    username = session.get('email')  
    full_name = session.get('full_name') 
    return render_template('manage-account-security.html', username=username, full_name=full_name)

# @app.route('/referuser')
# def refer_user():
#     username = session.get('username')
#     full_name = session.get('full_name')
#     url = 'solanafortune/register'
#     return render_template('referuser.html', url=url, username=username, full_name=full_name)

@app.route('/referuser')
def refer_user():
    if 'user_id' not in session:
        flash('You need to login first.', 'success')
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session.get('username')
    full_name = session.get('full_name')
    url = 'solanafortune.net/register'

    # Fetch the user's referrals
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT username, full_name, email, date_joined
    FROM users
    WHERE ref_by = %s
    """
    cursor.execute(query, (user_id,))
    referrals = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('referuser.html', url=url, username=username, full_name=full_name, referrals=referrals)

@app.route('/account_history')
def account_history():
    email = session.get('username')
    username = session.get('email')  
    full_name = session.get('full_name')  
    return render_template('account_history.html', username=username, full_name=full_name, email = email)

@app.route('/my_investment')
def my_investment():
    username = session.get('email')  
    full_name = session.get('full_name')  
    return render_template('my_investment.html', username=username, full_name=full_name)

if __name__ == '__main__':
    app.run(debug=True)