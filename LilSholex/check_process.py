import subprocess
if (result := len(subprocess.check_output(
        'ps -Af | grep "python manage.py process_tasks --sleep 1.5"', shell=True
).decode().strip().split('\n'))) != 4:
    exit(1)
