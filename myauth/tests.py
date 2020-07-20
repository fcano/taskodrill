from django.test import TestCase
from django.urls import reverse

class MyUserViews(TestCase):
    def test_signup_view(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password confirmation")