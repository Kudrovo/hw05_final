from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Follow, Group, Post, User
from posts.forms import PostForm
from posts.constants import (
    NUMBER_OF_POSTS_PER_PAGE, VIEWS_TEST_FOR_SECOND_PAGE,
    RANGE_FOR_TEST_PAGINATOR)


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='person')
        cls.user1 = User.objects.create_user(username='second')
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group1 = Group.objects.create(
            title='test title1',
            slug='test-slug1',
            description='test description1'
        )
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)

    def test_authorized_client_template(self):
        """Проверяем шаблоны для авторизованнных пользователей"""
        cache.clear()
        urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            'posts/create_post.html'
        }
        for address, template in urls.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_author.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post.id, self.post.pk)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.id, self.post.pk)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            'posts:profile', kwargs={'username': self.post.author})
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.id, self.post.pk)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)
        author = response.context['author']
        self.assertEqual(author.username, self.user.username)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post = response.context['post']
        self.assertEqual(post.pk, self.post.pk)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:post_create'))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        post = response.context['post']
        self.assertEqual(post.pk, self.post.pk)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertEqual(post.group, self.group)
        is_edit = response.context['is_edit']
        self.assertEqual(is_edit, True)

    def test_created_post_shows_correct_on_index_page(self):
        """Cозданный пост корректно отображается на главной странице"""
        cache.clear()
        new_post = Post.objects.create(
            text='Тестовый текст1',
            author=self.user,
            group=self.group
        )
        response = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(new_post, response.context['page_obj'][0])

    def test_created_post_shows_correct_in_group_list(self):
        """Cозданный пост корректно отображается на странице группы"""
        new_post = Post.objects.create(
            text='Тестовый текст1',
            author=self.user,
            group=self.group
        )
        response = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(new_post, response.context['page_obj'][0])

    def test_created_post_shows_correct_on_profile_page(self):
        """Cозданный пост корректно отображается на странице автора"""
        new_post = Post.objects.create(
            text='Тестовый текст1',
            author=self.user,
            group=self.group
        )
        response = self.authorized_author.get(reverse(
            'posts:profile', kwargs={'username': self.post.author})
        )
        self.assertEqual(new_post, response.context['page_obj'][0])

    def test_post_created_not_in_incorrect_group(self):
        """Созданный пост не появляется в не заданной для группе"""
        first_post = Post.objects.create(
            text='Тестовый текст1',
            author=self.user,
            group=self.group
        )
        second_post = Post.objects.create(
            text='Тестовый текст2',
            author=self.user,
            group=self.group1
        )
        response = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={'slug': self.group1.slug}))
        self.assertNotEqual(first_post, response.context['page_obj'][0])
        self.assertEqual(second_post, response.context['page_obj'][0])

    def test_cache(self):
        post = Post.objects.get(id=1)
        response = self.authorized_author.get(reverse('posts:index'))
        data_cache = response.content
        post.delete()
        response = self.authorized_author.get(reverse('posts:index'))
        deleted_but_in_cache = response.content
        cache.clear()
        response = self.authorized_author.get(reverse('posts:index'))
        empty_cache = response.content
        self.assertEqual(data_cache, deleted_but_in_cache)
        self.assertNotEqual(deleted_but_in_cache, empty_cache)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='person2')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug2',
            description='test'
        )
        cls.posts_count = []
        for i in RANGE_FOR_TEST_PAGINATOR:
            cls.posts_count.append(Post(
                text=f'Тестовый текст {i}',
                author=cls.user,
                group=cls.group
            ))
        cls.posts = Post.objects.bulk_create(cls.posts_count)

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """На первой странице отображается десять записей"""
        views_responses = {
            self.client.get(reverse('posts:index')): NUMBER_OF_POSTS_PER_PAGE,
            self.client.get(reverse(
                'posts:group_list', kwargs={'slug': self.group.slug})):
                    NUMBER_OF_POSTS_PER_PAGE,
            self.client.get(reverse(
                'posts:profile', kwargs={'username': self.user.username})):
                    NUMBER_OF_POSTS_PER_PAGE,
        }
        for responses, number in views_responses.items():
            with self.subTest(responses=responses):
                response = responses.context['page_obj']
                self.assertEqual(len(response), number)

    def test_second_page_contains_three_records(self):
        """На второй странице отображается три записи"""
        views_responses = {
            self.client.get(reverse('posts:index') + '?page=2'):
                VIEWS_TEST_FOR_SECOND_PAGE,
            self.client.get(reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}) + '?page=2'):
                    VIEWS_TEST_FOR_SECOND_PAGE,
            self.client.get(reverse(
                'posts:profile', kwargs={
                    'username': self.user.username}) + '?page=2'):
                    VIEWS_TEST_FOR_SECOND_PAGE,
        }
        for responses, number in views_responses.items():
            with self.subTest(responses=responses):
                response = responses.context['page_obj']
                self.assertEqual(len(response), number)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user2 = User.objects.create_user(username='third')
        cls.user3 = User.objects.create_user(username='forth')
        cls.user4 = User.objects.create_user(username='fifth')
        cls.post2 = Post.objects.create(
            text='Новый тестовый текст',
            author=cls.user3)
        cls.post3 = Post.objects.create(
            text='Новый тестовый текст1',
            author=cls.user4)

    def setUp(self):
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.user2)
        self.author_client.force_login(self.user3)
        cache.clear()

    def test_following(self):
        url = f'/profile/{self.user3.username}/follow/'
        self.authorized_client.get(url)
        cache.clear()
        self.assertTrue(Follow.objects.filter(
            user=self.user2, author=self.user3).exists())

    def test_unfollow(self):
        cache.clear()
        url = f'/profile/{self.user3.username}/follow/'
        unfollow_url = f'/profile/{self.user3.username}/unfollow/'
        self.authorized_client.get(url)
        self.authorized_client.get(unfollow_url)
        cache.clear()
        self.assertFalse(Follow.objects.filter(
            user=self.user2, author=self.user3).exists())

    def test_followed_author_post_on_index(self):
        cache.clear()
        url = f'/profile/{self.user3.username}/follow/'
        self.authorized_client.get(url)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context.get('page_obj')[0], self.post2)
