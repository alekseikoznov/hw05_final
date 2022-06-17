import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, Group, Comment
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        TEXT_OF_POST = 'Другой тестовый пост'
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': TEXT_OF_POST,
            'group': PostFormTests.group.pk,
            'author': PostFormTests.user.username,
            'image': uploaded
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        created_post = Post.objects.first()
        self.assertEqual(created_post.text, form_data['text'])
        self.assertEqual(created_post.group.pk, form_data['group'])
        self.assertEqual(created_post.author.username, form_data['author'])
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': PostFormTests.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        NEW_TEXT_OF_POST = 'Измененный тестовый пост'
        form_data = {
            'text': NEW_TEXT_OF_POST,
            'group': PostFormTests.group.pk,
            'author': PostFormTests.user.username
        }
        response = PostFormTests.authorized_author.post(
            reverse('posts:post_edit', args=(PostFormTests.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                author=PostFormTests.user,
                group=PostFormTests.post.group,
                text=NEW_TEXT_OF_POST).exists())

    def test_add_comment_user(self):
        """Пользователь может оставлять комментарии."""
        form_data = {
            'text': 'комментарий'
        }
        PostFormTests.authorized_author.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertTrue(Comment.objects.filter(text='комментарий'))

    def test_add_comment_guest(self):
        """Гость не может оставлять комментарии."""
        form_data = {
            'text': 'Я гость'
        }
        self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertFalse(Comment.objects.filter(text='Я гость'))
