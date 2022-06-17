import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group_slug',
            description='Тестовое описание',
        )
        cls.group_empty = Group.objects.create(
            title='Пустая группа',
            slug='group_empty',
            description='Пустая группа',
        )
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
        cls.post_1 = Post.objects.create(
            text='Текст1.',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user_client = User.objects.create_user(username='User_client')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_client)
        self.user_1 = User.objects.create_user(username='Followtest')
        self.authorized_user_1 = Client()
        self.authorized_user_1.force_login(self.user_1)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'group_slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'HasNoName'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_first_post(self, response):
        first_post = response.context['page_obj'][0]
        test_contex = {
            first_post.text: PostsViewsTests.post_1.text,
            first_post.author: PostsViewsTests.post_1.author,
            first_post.group.slug: PostsViewsTests.group.slug,
            first_post.image: PostsViewsTests.post_1.image
        }
        return test_contex

    def test_index_page_uses_correct_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        test_contex = self.check_first_post(response)
        for request, value in test_contex.items():
            with self.subTest(value=value):
                self.assertEqual(request, value)

    def test_group_correct_context(self):
        """Шаблон группы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'group_slug'}))
        test_contex = self.check_first_post(response)
        for request, value in test_contex.items():
            with self.subTest(value=value):
                self.assertEqual(request, value)

    def test_profile_correct_context(self):
        """Шаблон профиля сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'HasNoName'}))
        posts_count = response.context['posts_count']
        test_contex = self.check_first_post(response)
        for request, value in test_contex.items():
            with self.subTest(value=value):
                self.assertEqual(request, value)
        self.assertEqual(posts_count, PostsViewsTests.user.posts.count())

    def test_post_detail_correct_context(self):
        """Шаблон информации о посте сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id': '1'}))
        posts = response.context['posts']
        posts_count = response.context['posts_count']
        self.assertEqual(posts.text, PostsViewsTests.post_1.text)
        self.assertEqual(posts_count, PostsViewsTests.user.posts.count())
        self.assertEqual(posts.image, PostsViewsTests.post_1.image)

    def test_post_edit_correct_context(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = PostsViewsTests.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_correct_context(self):
        """Шаблон создания поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_correct_place_of_post(self):
        """Пост находится на предполагаемой странице."""
        page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'group_slug'}),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
        ]
        for page in page_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                post1 = response.context['page_obj']
                self.assertIn(PostsViewsTests.post_1, post1)

    def test_not_correct_place_of_post(self):
        """Пост не находится в той группе, в которую не записан."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group_empty'}))
        posts_in_page = response.context['page_obj']
        self.assertNotIn(PostsViewsTests.post_1, posts_in_page)

    def test_cache_index_page(self):
        """Главная страница хранится в кэше 20 секунд."""
        TEXT_FOR_POST = 'Текст2.'
        post =  Post.objects.create(
            text=TEXT_FOR_POST,
            author=PostsViewsTests.user,
            group=PostsViewsTests.group,
        )
        response_before = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        response_after = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(response_before, response_after)
        cache.clear()
        response_after = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(response_before, response_after)

    def test_auth_user_follow(self):
        """Пользователь может подписываться и отписываться."""
        follow = Follow.objects.create(
                user=self.user_client,
                author=PostsViewsTests.user)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_client,
                author=PostsViewsTests.user
            ).exists()
        )
        follow.delete()
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_client,
                author=PostsViewsTests.user
            ).exists()
        )

    def test_follow_on_yourself(self):
        """Пользователь не может подписываться на себя."""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'User_client'}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_client,
                author=self.user_client
            ).exists()
        )

    def count_pages_follow(self, user_test):
        response = user_test.get(
            reverse('posts:follow_index'))
        return len(response.context['page_obj'])

    def test_new_post_in_follow(self):
        """В ленту подписчика добавляются посты."""
        TEXT_FOR_POST = 'Текст2.'
        Follow.objects.create(
                user=self.user_1,
                author=PostsViewsTests.user)
        count_before_follower = self.count_pages_follow(self.authorized_user_1)
        count_before = self.count_pages_follow(self.authorized_client)
        Post.objects.create(
            text=TEXT_FOR_POST,
            author=PostsViewsTests.user,
            group=PostsViewsTests.group,
        )
        count_after_follower = self.count_pages_follow(self.authorized_user_1)
        count_after = self.count_pages_follow(self.authorized_client)
        self.assertNotEqual(count_before_follower, count_after_follower)
        self.assertEqual(count_before, count_after)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        objs = [
            Post(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group
            )
            for i in range(1, 14)
        ]
        Post.objects.bulk_create(objs)

    def len_of_page(self, link):
        response = PaginatorViewsTest.authorized_client.get(link)
        return len(response.context['page_obj'])

    def test_first_page_contains_ten_records(self):
        """Проверка количества постов на странице: 10."""
        LEN_PAGE_1 = 10
        pages = {reverse('posts:group_list',
                         kwargs={'slug': 'test-slug'}): LEN_PAGE_1,
                 reverse('posts:index'): LEN_PAGE_1,
                 reverse('posts:profile',
                         kwargs={'username': 'auth'}): LEN_PAGE_1
                 }
        for request, value in pages.items():
            with self.subTest(value=value):
                self.assertEqual(self.len_of_page(request), value)

    def test_second_page_contains_three_records(self):
        """Проверка количества постов на странице: 3."""
        LEN_PAGE_2 = 3
        pages = {reverse('posts:group_list',
                         kwargs={'slug': 'test-slug'}): LEN_PAGE_2,
                 reverse('posts:index'): LEN_PAGE_2,
                 reverse('posts:profile',
                         kwargs={'username': 'auth'}): LEN_PAGE_2
                 }
        for request, value in pages.items():
            with self.subTest(value=value):
                self.assertEqual(self.len_of_page(request + '?page=2'),
                                 value)
