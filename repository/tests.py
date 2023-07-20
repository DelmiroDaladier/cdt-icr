from datetime import datetime
from django.test import TestCase

from .forms import AuthorForm, ArxivForm, PublicationForm, VenueForm
from .models import ResearchArea, Author, Venue, Publication, Conference, Session

# Create your tests here.

class RepositoryTest(TestCase):

    def create_research_area(self, title='research area'):
        return ResearchArea.objects.create(title=title)

    def create_author(self, user='Test User'):
        return Author.objects.create(user=user)
    
    def create_venue(self, venue_name='venue_name'):
        return Venue.objects.create(venue_name=venue_name)

    def create_conference(self, venue_name='conference_name', location='conference_location', start_date='01/12/2023', end_date='05/12/2023'):
        return Conference.objects.create(
            venue_name=venue_name,
            location=location,
            start_date=datetime.strptime(start_date, '%d/%m/%Y'),
            end_date=datetime.strptime(end_date, '%d/%m/%Y')
        )

    def create_session(self, type='Tutorial', start_date='01/12/2023', end_date='05/12/2023'):
        conference = self.create_conference()

        return Session.objects.create(
            conference=conference,
            type=type,
            start_date=datetime.strptime(start_date, '%d/%m/%Y'),
            end_date=datetime.strptime(end_date, '%d/%m/%Y')
        )

    def create_publication(self, name='publication_name', overview='publication_overview'):
        authors = self.create_author()
        research_area = self.create_research_area()
        publication =  Publication.objects.create(
            name=name,
            overview=overview
        )

        publication.authors.add(authors)
        publication.research_area.add(research_area)
        
        return publication

    def test_research_area_creation(self):
        research_area = self.create_research_area()
        self.assertTrue(isinstance(research_area, ResearchArea)) 

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
        data = {
            'user': 'User'
        }
        form = AuthorForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_author_form_is_not_valid(self):
        data = {
            'user': ''
        }
        form = AuthorForm(data=data)
        self.assertFalse(form.is_valid())

    def test_venue_form_is_valid(self):
        data = {
            'venue_name': 'Venue Name'
        }
        form = VenueForm(data=data)
        self.assertTrue(form.is_valid())

    def test_venue_form_is_not_valid(self):
        data = {
            'venue_name': 'Venue Name',
            'venue_url': 'a_wrong_url'
        }
        form = VenueForm(data=data)
        self.assertFalse(form.is_valid())