### Heroku 배포 시  발생된 에러

```
remote: ! Error while running '$ python manage.py collectstatic --noinput'.
remote:   See traceback above for details.
remote: 
remote:   You may need to update application code to resolve this error.
remote:   Or, you can disable collectstatic for this application:

```

### Solution : 

1. `heroku config:set DISABLE_COLLECTSTATIC=1`

2. `git push heroku master`

3. `heroku run python manage.py migrate` 

   -> ModuleNotFoundError: No module named 'storages'

4. ```heroku run 'bower install --config.interactive=false;grunt prep;python manage.py collectstatic —noinput'```

5. `heroku config:unset DISABLE_COLLECTSTATIC`

6. `heroku run python manage.py collectstatic`