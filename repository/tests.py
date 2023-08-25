import unittest
from selenium import webdriver
from selenium.webdriver.common.by import (
    By,
)
from selenium.webdriver.chrome.service import (
    Service,
)
from selenium.webdriver.support.wait import (
    WebDriverWait,
)
from selenium.webdriver.support import (
    expected_conditions as EC,
)
from django.contrib.staticfiles.testing import (
    StaticLiveServerTestCase,
)

from datetime import datetime
from django.urls import reverse
from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.models import (
    User,
)
from django.contrib.sessions.backends.db import (
    SessionStore,
)
from django.contrib.auth import (
    SESSION_KEY,
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
)

from .views import (
    homepage,
    about,
    author_create,
    add_category,
    add_venue,
    arxiv_post,
    submit_conference,
    submit_session,
)
from .models import (
    ResearchArea,
    Author,
    Venue,
    Publication,
    Conference,
    Session,
)
from .forms import (
    AuthorForm,
    PublicationForm,
    VenueForm,
    ResearchAreaForm,
    ConferenceForm,
)

# Create your tests here.


def create_session_cookie(username, password):
    # First, create a new test user
    user = User.objects.create_user(
        username=username,
        password=password,
    )

    # Then create the authenticated session using the new user credentials
    session = SessionStore()
    session[SESSION_KEY] = user.pk
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()

    # Finally, create the cookie dictionary
    cookie = {
        "name": settings.SESSION_COOKIE_NAME,
        "value": session.session_key,
        "secure": False,
        "path": "/",
    }
    return cookie


class RepositoryTest(TestCase):
    def create_research_area(self, title="research area"):
        return ResearchArea.objects.create(title=title)

    def create_author(self, user="Test User"):
        return Author.objects.create(user=user)

    def create_venue(self, venue_name="venue_name"):
        return Venue.objects.create(venue_name=venue_name)

    def create_conference(
        self,
        venue_name="conference_name",
        location="conference_location",
        start_date="01/12/2023",
        end_date="05/12/2023",
    ):
        return Conference.objects.create(
            venue_name=venue_name,
            location=location,
            start_date=datetime.strptime(start_date, "%d/%m/%Y"),
            end_date=datetime.strptime(end_date, "%d/%m/%Y"),
        )

    def create_session(
        self,
        type="Tutorial",
        start_date="01/12/2023",
        end_date="05/12/2023",
    ):
        conference = self.create_conference()

        return Session.objects.create(
            conference=conference,
            type=type,
            start_date=datetime.strptime(start_date, "%d/%m/%Y"),
            end_date=datetime.strptime(end_date, "%d/%m/%Y"),
        )

    def create_publication(
        self,
        name="publication_name",
        overview="publication_overview",
    ):
        authors = self.create_author()
        research_area = self.create_research_area()
        publication = Publication.objects.create(
            name=name,
            overview=overview,
        )

        publication.authors.add(authors)
        publication.research_area.add(research_area)

        return publication

    def test_research_area_creation(
        self,
    ):
        research_area = self.create_research_area()
        self.assertTrue(
            isinstance(
                research_area,
                ResearchArea,
            )
        )

    def test_author_creation(self):
        author = self.create_author()
        self.assertTrue(isinstance(author, Author))

    def test_venue_creation(self):
        venue = self.create_venue()
        self.assertTrue(isinstance(venue, Venue))

    def test_conference_creation(self):
        conference = self.create_conference()
        self.assertTrue(isinstance(conference, Conference))

    def test_session_creation(self):
        session = self.create_session()
        self.assertTrue(isinstance(session, Session))

    def test_publication_creation(self):
        publication = self.create_publication()
        self.assertTrue(isinstance(publication, Publication))

    def test_author_form_is_valid(self):
        data = {"user": "User"}
        form = AuthorForm(data=data)
        self.assertTrue(form.is_valid())

    def test_author_form_is_not_valid(
        self,
    ):
        data = {"user": ""}
        form = AuthorForm(data=data)
        self.assertFalse(form.is_valid())

    def test_venue_form_is_valid(self):
        data = {"venue_name": "Venue Name"}
        form = VenueForm(data=data)
        self.assertTrue(form.is_valid())

    def test_venue_form_is_not_valid(
        self,
    ):
        data = {
            "venue_name": "Venue Name",
            "venue_url": "a_wrong_url",
        }
        form = VenueForm(data=data)
        self.assertFalse(form.is_valid())

    def test_research_area_is_valid(
        self,
    ):
        data = {"title": "Research Area Title"}
        form = ResearchAreaForm(data=data)
        self.assertTrue(form.is_valid())

    def test_research_area_is_not_valid(
        self,
    ):
        data = {"title": ""}
        form = ResearchAreaForm(data=data)
        self.assertFalse(form.is_valid())

    def test_publication_form_is_valid(
        self,
    ):
        author = self.create_author()
        research_area = self.create_research_area()
        venue = self.create_venue()

        data = {
            "name": "publication title",
            "overview": "overview text",
            "authors": [author],
            "research_area": [research_area],
            "venue": [venue],
        }
        form = PublicationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_publication_form_is_not_valid(
        self,
    ):
        research_area = self.create_research_area()
        venue = self.create_venue()

        data = {
            "name": "publication title",
            "overview": "overview text",
            "authors": [],
            "research_area": [research_area],
            "venue": [venue],
        }
        form = PublicationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_conference_form_is_valid(
        self,
    ):
        data = {
            "venue_url": "http://genericurl.com",
            "venue_name": "Venue Name",
            "start_date": "07/22/23",
            "end_date": "07/25/23",
            "location": "Here",
        }
        form = ConferenceForm(data=data)
        self.assertTrue(form.is_valid())

    def test_conference_form_is_not_valid(
        self,
    ):
        data = {
            "venue_url": "genericurl.com",
            "venue_name": "Venue Name",
            "start_date": "07/22/23",
            "end_date": "07/25/23",
            "location": "Here",
        }
        form = ConferenceForm(data=data)
        self.assertFalse(form.is_valid())

    def test_authentication_required(
        self,
    ):
        url = reverse(homepage)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["location"],
            "/accounts/login/?next=/",
        )

    def test_homepage_view(self):
        url = reverse(homepage)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_about_view(self):
        url = reverse(about)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_author_create_view(self):
        url = reverse(author_create)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_add_research_area_view(
        self,
    ):
        url = reverse(add_category)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_add_venue_view(self):
        url = reverse(add_venue)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_arxiv_post_view(self):
        url = reverse(arxiv_post)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_submit_conference_view(
        self,
    ):
        url = reverse(submit_conference)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_submit_session_view(self):
        url = reverse(submit_session)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)



