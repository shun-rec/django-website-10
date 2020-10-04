# djangoチュートリアル #10 サインアップ

## 最小コードで実用的なサインアップを作ろう！

## 完成版プロジェクト

<https://github.com/shun-rec/django-website-10>

## 事前準備

前回から引き続き実装している方は事前準備は不要です。

### 前回ログインを作ったプロジェクトをダウンロード

```sh
git clone https://github.com/shun-rec/django-website-09.git
cd django-website-09
```

* ユーザー名: admin
* メールアドレス: dev@example.com
* パスワード: admin

### 動かしてみよう

開発サーバーを立ち上げて、以下４つの機能が動いていたらOKです。

* ログイン
* ログアウト
* パスワード変更
* パスワード再設定

## ステップ１：メールアドレス必須のユーザー登録フォーム

djangoデフォルトのユーザーモデルは、メールアドレスが必須ではありません。  
さらに、他のユーザーと同じメールアドレスも登録できてしまいます。  
本番ではメールアドレスは必須で他のユーザーと被らないようにしたいのでカスタマイズします。

### ユーザーモデルの作成

自作のユーザーモデルを作るには、djangoの`AbstractUser`を継承します。  
ユーザー名やパスワードはデフォルトのままで、`email`だけ自分で上書き定義します。  
`unique=True`を指定するとメールアドレスがユーザー固有（一意）のものになります。

`registration/models.py`を以下の内容に修正。

```py
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField('メールアドレス', unique=True)
```

**※たとえカスタマイズしなくても独自のユーザーモデルを定義しておくのがベストプラクティスです！**

### 自作のユーザーモデルをプロジェクトのユーザーモデルとして指定

指定しないとdjangoで使われません。

全体設定ファイル`pj_login/settings.py`の最後に以下を追記。

```py
AUTH_USER_MODEL = 'registration.User'
```

### サインアップフォームを作成

`registration/forms.py`を以下の内容で作成。

```py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.conf import settings

User = get_user_model()


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        # commit=Falseだと、DBに保存されない
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.save()
        return user
```

* ユーザーモデルにアクセスする時には`from .models import User`などではなく、必ず`get_user_model`で取得します。
  * 開発中に`AUTH_USER_MODEL`が切り替わったときなどにエラーになるため。
* djangoデフォルトのサインアップフォームは`UserCreationForm`で、これをカスタマイズします。
* `email`の設定でエラーになると中途半端なユーザーが出来てしまうので、`email`の設定が出来て初めてユーザーを保存します。

### ビューを作成

`registration/views.py`を以下の内容で作成。

```py
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

from .forms import SignUpForm


class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
```

* `CreateView`を使うとフォームを表示し、データを保存するところまで自動で行ってくれます。

### テンプレート作成

`registration/templates/registration/signup.html`を以下の内容で新規作成。

```html
{% extends "base.html" %}
{% block main %}
{% include "_form.html" with submit_label="登録" %}
{% endblock %}
```

### URLの設定

`pj_login/urls.py`に以下のインポートを追加。

```py
from registration import views
```

`urlpatterns`の最後に以下を追加。

```py
    path("signup/", views.SignUpView.as_view(), name="signup"),
```

### ログイン画面の一番下にサインアップへのリンクを追加

`registration/templates/registration/login.html`の`main`ブロックの一番下に以下を追記。

```html
<p><a href="{% url 'signup' %}">サインアップ</a></p>
```

### データベースの作成

※ 前回から引き続いて実装している方は一度データベースを削除して下さい（sqlite3を使用している場合は`db.sqlite3`ファイルを削除）。

```sh
python manage.py migrate
```

### 動かしてみよう

開発サーバーを起動して、サインアップページにアクセスしてみましょう。  
サインアップしたユーザーでログイン出来たらOKです。  
メールアドレスが空欄の場合にはエラーが出るはずです。

## ステップ２：ユーザー登録時にメールを送ろう

メールアドレスは登録出来ましたが、このままではそのメールアドレスの持ち主が本当にそのユーザーかどうかを確かめる方法がありません。  
メールアドレス宛に認証用URLを送って登録を完了させるようにしましょう。  
まずは認証メールを送ってみましょう。

### メールに記載するサイトのURLを設定

`pj_login/settings.py`の末尾に以下を追加。

```py
FRONTEND_URL = "https://localhost-shundev-1.paiza-user-free.cloud:8000"
```

* 変数名は何でもいいですが、URLの部分は自身の環境に合わせて変えて下さい。（ローカルで開発している場合はhttp://localhost:8000など）

### フォーム保存完了時に認証メールを送信

`registration/forms.py`に以下のインポートを追加。

```py
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
```

* ３つともこの用途でしかほとんど使いません。テンプレとして覚えてOKです。

`SignUpForm`の上に以下を追加。

```py
subject = "登録確認"
message_template = """
ご登録ありがとうございます。
以下URLをクリックして登録を完了してください。

"""

def get_activate_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return settings.FRONTEND_URL + "/activate/{}/{}/".format(uid, token)
```

* uidとtokenは認証URLの作成に必要なものです。テンプレとして覚えてしまいましょう！
* get_activate_url関数でURLを組み立てて返しています。

`SignUpForm`の`save`メソッドを以下のように修正。

```py
    def save(self, commit=True):
        # commit=Falseだと、DBに保存されない
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        
        # 確認するまでログイン不可にする
        user.is_active = False
        
        if commit:
            user.save()
            activate_url = get_activate_url(user)
            message = message_template + activate_url
            user.email_user(subject, message)
        return user
```

* `user.is_active = False`とすることで、メールで認証するまでログイン不可としています。
* `commit=True`の場合だけユーザーを保存し、メールを送信します。（ウェブからフォームを送信すると自動でTrueになります）
* `user.email_user`でそのユーザー１人にメールを送ることが出来ます。

### 動かしてみよう

サインアップしてコンソールを確認し、認証URLが届いていたらOKです。

## 認証URLで認証しよう

あとは認証URLをクリックした時にユーザーを有効可するだけです。

### 認証ロジックを作成

`registration/forms.py`の末尾に以下を追加。

```py
def activate_user(uidb64, token):    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        return False

    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return True
    
    return False
```

* URLで渡されたuidb64とtokenで認証します。
* テンプレとして覚えてしまいましょう！

### 認証ビューの作成

認証OKならユーザーを有効化しましょう。

`registration/views.py`のインポートに以下を追加。

```py
from django.views.generic import TemplateView
from .forms import activate_user
```

以下の認証用ビューを追加。

```py
class ActivateView(TemplateView):
    template_name = "registration/activate.html"
    
    def get(self, request, uidb64, token, *args, **kwargs):
        # 認証トークンを検証して、
        result = activate_user(uidb64, token)
        # コンテクストのresultにTrue/Falseの結果を渡します。
        return super().get(request, result=result, **kwargs)
```

### テンプレートの作成

```html
{% extends "base.html" %}
{% block main %}
{% if result %}
    <p>認証に成功しました。</p>
    <p><a href="{% url 'login' %}">ログイン</a></p>
{% else %}
    <p>無効なリンクです。</p>
{% endif %}
{% endblock %}
```

### 動かしてみよう

サインアップ → メールのURLクリック → アカウント有効化 → ログインが一通り出来ればOKです。
