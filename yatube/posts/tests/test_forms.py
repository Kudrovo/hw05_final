import tempfile

from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='person3')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug3',
            description='test group description'
        )
        cls.group1 = Group.objects.create(
            title='second group',
            slug='test-slug4',
            description='new group description'
        )

    def setUp(self):
        super().setUpClass()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """При отправке формы создания поста создается новая запись в БД"""
        count = Post.objects.count()
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
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image.name, 'posts/' + form_data['image'].name)

    def test_post_edit(self):
        """При отправке формы редактирования поста он изменятеся в БД"""
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=small_gif,
            content_type='image/gif'
        )
        count = Post.objects.count()
        new_post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Новый текст',
            'group': self.group1.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id':
                    new_post.pk}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=new_post.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), count + 1)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': edited_post.pk}))
        self.assertEqual(edited_post.author, self.user)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
        self.assertEqual(
            edited_post.image.name, 'posts/' + form_data['image'].name)

    def test_add_comment_by_authorized_user(self):
        """При отправке формы комментария он появится под постом"""
        comments_count = Comment.objects.count()
        new_post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group1
        )
        form_data_comment = {
            'text': 'comment'
        }
        post_comment = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': new_post.pk}),
            data=form_data_comment,
            follow=True
        )
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': new_post.pk}))
        comment = response.context.get('comments')[0]
        comment_obj = Comment.objects.first()
        self.assertEqual(post_comment.status_code, 200)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment_obj.post, comment.post)
        self.assertEqual(comment_obj.text, comment.text)
        self.assertEqual(comment_obj.author, comment.author)

    def test_redirect_guest_user_trying_to_comment(self):
        """При отправке формы, неавторизированный клиент будет перенаправлен"""
        comments_count = Comment.objects.count()
        new_post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group1
        )
        form_data_comment = {
            'text': 'comment'
        }
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': new_post.pk}),
            data=form_data_comment,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse(
                'posts:add_comment', kwargs={'post_id': new_post.pk}))
        self.assertEqual(Comment.objects.count(), comments_count)
