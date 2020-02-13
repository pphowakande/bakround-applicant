restart:
	docker-compose down && docker-compose build && (docker-compose up &)

start: restart

stop:
	docker-compose down

test:
	docker-compose run django ./scripts/tests/run-tests.sh ${TEST_DIR}

coverage:
	docker-compose run django ./scripts/tests/run-coverage.sh

migrations:
	docker-compose run django ./scripts/utilities/manage.py makemigrations

migrate:
	docker-compose run django ./scripts/utilities/manage.py migrate

superuser:
	docker-compose run django ./scripts/utilities/manage.py createsuperuser

shell:
	docker-compose run django ./scripts/utilities/manage.py shell

check_constraints:
	! pip freeze | grep -vxiF -f requirements/constraint.txt -
