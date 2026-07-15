from django.contrib.auth.mixins import UserPassesTestMixin


class DonoOuAdminMixin(UserPassesTestMixin):
    """Libera o objeto para quem o criou e para quem tem is_staff.

    O handle_no_permission() do AccessMixin ja faz a distincao certa sozinho:
    levanta PermissionDenied (403) para usuario autenticado e redireciona
    anonimo para o login. Nao mexa em raise_exception.
    """

    def test_func(self):
        return self.get_object().criado_por == self.request.user or self.request.user.is_staff
