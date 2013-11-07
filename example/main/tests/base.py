from django.test import TestCase


class BaseTestCase(TestCase):

    def test_response(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        from django.contrib.auth.models import User

        user = User.objects.create(username='testuser')
        user.set_password('testpassword')
        user.save()

        self.client.login(username='testuser', password='testpassword')

        response = self.client.get('/')
        self.assertContains(response, 'logout')

        response = self.client.get('/logout', follow=True)
        self.assertNotContains(response, 'logout')
