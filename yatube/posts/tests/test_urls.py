from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Post, Group
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user_1 = User.objects.create_user(username='HasNoName')
        self.authorized_user_1 = Client()
        self.authorized_user_1.force_login(self.user_1)

    def test_urls_for_guest_client(self):
        """Страницы, которые доступны любому пользователю."""
        urls = ['/', '/group/test-slug/', '/posts/1/']
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_authorized_client(self):
        """Страницы, которые доступны авторизованному пользователю."""
        urls = ['/create/', '/posts/1/edit/']
        for url in urls:
            with self.subTest(url=url):
                response = PostURLTests.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = PostURLTests.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_page(self):
        """Проверка редиректа для страницы редкатирования поста."""
        response = self.guest_client.get('/posts/1/edit/')
        response_user = self.authorized_user_1.get('/posts/1/edit/')
        self.assertRedirects(
            response, ('/posts/1/'))
        self.assertRedirects(
            response_user, ('/posts/1/'))

    def test_create_post_page(self):
        """Проверка редиректа для страницы создания поста."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def test_comment_post(self):
        """Проверка редиректа для комментирования поста."""
        response = self.guest_client.get('/posts/1/comment/')
        response_user = self.authorized_user_1.get('/posts/1/comment/')
        self.assertRedirects(
            response, ('/auth/login/?next=/posts/1/comment/'))
        self.assertRedirects(
            response_user, ('/posts/1/'))

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_template(self):
        """Тестирование кастомного шаблона 404."""
        template = 'core/404.html'
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, template)
