import datetime
import pytest
from flask_login import FlaskLoginClient

from app import create_app, db
from app.models import Reservation, User, rentalvehicle
from tests.testconf import TestConfig


@pytest.fixture
def testApp():
    app = create_app(TestConfig)
    app.test_client_class = FlaskLoginClient
    with app.app_context():
        db.create_all()
        # Create default rental vehicles
        for x in range(1, 4):
            vehicle = rentalvehicle(id=x, price=5, info=f"vehicles {x}")
            db.session.add(vehicle)
        db.session.commit()

        u = User(username="toby")
        u.set_password("kali")
        db.session.add(u)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(testApp):
    user = User.query.filter_by(username="toby").first()
    return testApp.test_client(user=user)


class Testrental:
    @pytest.mark.dependency()
    def test_reserve_model(self, testApp):  # noqa: F811
        today = datetime.date.today()
        vehicle = rentalvehicle.query.filter_by(id=1).first()
        vehicle.reserve(today, User.query.filter_by(username="toby").first())
        assert vehicle.is_reserved(today)

    @pytest.mark.dependency()
    def test_free_model(self, testApp):  # noqa: F811
        today = datetime.date.today()
        vehicle = rentalvehicle.query.filter_by(id=1).first()
        vehicle.reserve(today, User.query.filter_by(username="toby").first())
        userReservation = vehicle.free(
            today, User.query.filter_by(username="toby").first()
        )
        assert userReservation is not None

    @pytest.mark.dependency(
        depends=[
            "Testrental::test_reserve_model",
            "Testrental::test_free_model",
        ]
    )
    def test_reserve_route(self, client, testApp):
        today = datetime.date.today()
        with client:
            response = client.post(f"/reserve/1/{today.isoformat()}")
        assert response.status_code == 302
        with testApp.app_context():
            assert Reservation.query.filter_by(date=today).first() is not None

    @pytest.mark.dependency(
        depends=[
            "Testrental::test_reserve_model",
            "Testrental::test_free_model",
            "Testrental::test_reserve_route",
        ]
    )
    def test_free_route(self, client, testApp):
        today = datetime.date.today()
        with client:
            response = client.post(f"/reserve/1/{today.isoformat()}")
        with testApp.app_context():
            assert Reservation.query.filter_by(date=today).first() is not None

        with client:
            response = client.post(f"/free/1/{today.isoformat()}")
        assert response.status_code == 302
        with testApp.app_context():
            assert Reservation.query.filter_by(date=today).first() is None