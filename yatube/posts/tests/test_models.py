from django.test import TestCase

from posts.models import Group, Post, User
from posts.constants import TEXT_OUTPUT


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        model_objects = {
            self.post.text[:TEXT_OUTPUT]: self.post,
            self.group.title: self.group
        }
        for attribute, object in model_objects.items():
            with self.subTest(object=object):
                self.assertEqual(attribute, str(object))
