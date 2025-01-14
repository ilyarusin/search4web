from flask import Flask, render_template, request, session, copy_current_request_context
from markupsafe import escape
from vsearch import search4letters
from checker import check_logged_in
from DBcm import UseDatabase, ConnectionError, CredentialsError, SQLError
from threading import Thread

app = Flask(__name__)

app.config['dbconfig'] = { 'host': '',
                            'user': '',
                            'password': '',
                            'database': 'vsearchlogDB', }


@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in (Теперь вы в системе)'

@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in', None)
    return 'You are now logged out (Вы теперь не в системе)'


@app.route('/search4', methods=['POST'])
def do_search() -> 'html':

    @copy_current_request_context
    def log_request(req: 'flask_request', res: str) -> None:
        """Журналирует веб-запрос и возвращаемые результаты."""
        
        try:
            with UseDatabase(app.config['dbconfig']) as cursor:
                _SQL = """insert into log 
                        (phrase, letters, ip, browser_string, results)
                        values
                        (%s, %s, %s, %s, %s)"""
                cursor.execute(_SQL, (req.form['phrase'], req.form['letters'], req.remote_addr, req.headers.get('User-Agent'), res, ))
        except ConnectionError as err:
            print('Is your DB switched on? Error:', str(err))
        except CredentialsError as err:
            print('User-id/Password issues. Error:', str(err))
        except SQLError as err:
            print('Is your query correct? Error:', str(err))
        except Exception as err:
            print('Something went wrong:', str(err))

    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are your results:'
    results = str(search4letters(phrase, letters))
    try:
        t = Thread(target=log_request, args=(request, results))
        t.start()
    except Exception as err:
        print('*** Логирование упало с этой ошибкой:', str(err))
    return render_template('results.html', the_title=title, the_results=results, the_phrase=phrase, the_letters=letters)

@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template('entry.html', the_title='Welcome to search4letters on the web!')

@app.route('/viewlog')
@check_logged_in
def view_the_log() -> 'html':
    """Отображает содержание лог файла в виде html таблицы."""
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """select phrase, letters, ip, browser_string, results from log"""
            cursor.execute(_SQL)
            contents = cursor.fetchall()
        titles = ('Phrase', 'Letters', 'Remote_addr', 'User_agent', 'Results')
        return render_template('viewlog.html', the_title='View Log', the_row_titles=titles, the_data=contents)
    except ConnectionError as err:
        print('Is your DB switched on? Error:', str(err))
    except CredentialsError as err:
        print('User-id/Password issues. Error:', str(err))
    except SQLError as err:
        print('Is your query correct? Error:', str(err))
    except Exception as err:
        print('Something went wrong:', str(err))
    return 'Error'

app.secret_key = 'YouWillNeverGuessMySecretKey'

if __name__ == '__main__':
    app.run(debug=True)