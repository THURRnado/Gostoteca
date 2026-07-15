from django.contrib.auth.mixins import UserPassesTestMixin


class DonoMixin(UserPassesTestMixin):
    """Libera o objeto apenas para quem o criou.

    Qual campo aponta para o dono varia por modelo: `Item` usa `criado_por`,
    `Review` usa `usuario`. Sobrescreva `campo_dono` na view.

    O handle_no_permission() do AccessMixin ja faz a distincao certa sozinho:
    levanta PermissionDenied (403) para usuario autenticado e redireciona
    anonimo para o login. Nao mexa em raise_exception.
    """

    campo_dono = 'criado_por'

    def test_func(self):
        return getattr(self.get_object(), self.campo_dono) == self.request.user


class DonoOuAdminMixin(DonoMixin):
    """Libera tambem para quem tem is_staff."""

    def test_func(self):
        return super().test_func() or self.request.user.is_staff
