from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='person1')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug1',
            description='test description'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)
        self.user1 = User.objects.create_user(username='notauthor')
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)

    def test_avaliable_pages_status_for_guest(self):
        """Проверяем статусы страниц доступных для гостей"""
        urls = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.FOUND
        }
        for address, status in urls.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, status)

    def test_pages_status_for_authorized_users(self):
        """Проверяем статусы страниц для авторизованных пользователей"""
        urls = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.OK
        }
        for address, status in urls.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertEqual(response.status_code, status)

    def test_unexpected_page(self):
        """Проверяем ссылку на несуществующую страницу"""
        response = self.client.get('/unexpected_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_correct_templates(self):
        """Проверяем шаблоны на соответствие ссылкам и доступность ссылок"""
        urls = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html'
        }
        for address, template in urls.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_redirect_anonymous(self):
        """Проверяем переадресацию из редактирования записи для гостей"""
        response = self.client.get(f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response, reverse('users:login') + '?next=' + reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk})
        )

    def test_edit_redirect_anonymous(self):
        """Проверяем переадресацию из создания новой записи для гостей"""
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, reverse('users:login') + '?next=' + reverse(
                'posts:post_create')
        )

    def test_create_redirect_not_author(self):
        """Проверяем переадресацию из редактирования записи для не ее автора"""
        response = self.authorized_client1.get(
            f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
