from textwrap import dedent


class Strings:
    HELP = dedent("""\
    <b> Бот для разделения чеков ФНС 🧾🇷🇺</b>
    
    <b>🤖 Что умеет этот бот?</b>
    С помощью этого бота вы можете разделить чек без долгих подсчётов на калькуляторе! 🤓
    
    <b>⁉ Как пользоваться ботом?</b>
    1. 🏦  Авторизируйтесь в ФНС по номеру телефона, введя /login.
    2. 👩🏼🧑👩🏿👳  Выберите, между кем следует разделить счёт, введя /new_receipt.
    3. 📸🧾  Отправьте боту фото чека, чтобы QR код был хорошо виден.
    4. 💸  Определите для каждой позиции, кто должен её оплатить.
    5. ✉  Перешли своим друзьям готовый итог! В нём будет написано, сколько каждый должен суммарно заплатить. 😃
    
    <b>🤔 Для чего нужна авторизация?</b>
    К сожалению, сервера ФНС ограничивают количество запросов в день на номер телефона. ✋
    Поэтому мы вынуждены просить вас авторизоваться, чтобы каждый пользователь имел свободный доступ к сервису. 😄
    """)

    START = dedent("""\
    Привет! 👋
    
    Этот бот поможет тебе разделить чек между друзьями по QR коду! 😎
    
    ℹ️  Подробная информация о боте доступна в /help. 
    
    Пожалуйста, введи свой номер телефона 📞, чтобы авторизоваться в ФНС и начать работу с ботом:
    """)

    EnterNames = dedent("""\
    👩🏼🧑👩🏿👳  В одном сообщении введи имена или ники друзей (не больше 10), между которыми ты хочешь разделить чек, по одному на каждой строке.
    
    Например: 
    
    Катя
    @durov
    Михал Палыч Терентьев
    """)

    UNAUTHORIZED_PLEASE_LOGIN = "🙁 Ты не авторизирован. Пожалуйста, залогинься: /login"

    EnterSMS = "📨 Введи код из СМС:"

    TooManyRequests = "🤯 Слишком много запросов. Пожалуйста, повтори попытку позже. Для повторной авторизации " \
                      "используй /login "

    InvalidPhone = "❌ Не удалось отправить СМС на указанный номер. Попробуй другой номер или повторите попытку позже." \
                   "Для повторной авторизации используй /login"

    InvalidPhoneTryAgain = "❌ Неверный формат номера телефона, попробуй ещё раз. Вводи номер в международном формате, " \
                           "например: +79001112233"

    BeginInteractionQrCode = "Введи команду /new_receipt, чтобы разделить чек."  # FIXME: start with qr directly

    InvalidCode = "❌ Код неверен. Попробуй ввести его ещё раз. Чтобы прекратить авторизацию, введите /cancel."

    HowToAuthenticate = "Для продолжения работы, пожалуйста, залогинься /login"

    OperationCancelled = "Операция отменена."

    rubles = "руб."

    SelectPeople = "Выбери людей, кто будет платить за этот товар"

    shallPay = "должен(-на) заплатить"

    RepeatInteractionQrCode = "Введи команду /new_receipt, чтобы отсканировать следующий чек."

    ResultsHeader = "🎉  Итог: "

    AdvertisingFooter = "👍  Чек был разделён с помощью @fns_check_bot"

    IncorrectFormat = "❌ Неверный формат ввода. Посмотри внимательно на пример и попробуй ещё раз. " \
                      "Чтобы отменить операцию, введи /cancel"

    EnterQR = "📸🧾  Пришли фотографию QR кода на чеке. " \
              "Постарайся, чтобы его было хорошо видно, и изображение было чётким."

    PleaseWait = "⏳  Пожалуйста, подождите..."  # TODO: `подожди` или `подождите`?

    FNSLoginError = "💥  На сервере ФНС что-то пошло не так... Пожалуйста, попробуй авторизоваться заново: /login. "

    CouldNotReadQR = "😕  Не удалось прочитать QR код. Пожалуйста, попробуй, ещё раз. " \
                     "Постарайся, чтобы его было хорошо видно, и изображение было чётким."

    Wrong = "Неверный ввод. Для отмены операции введи /cancel"

    Prev = "Назад"
    Next = "Дальше"
    Cancel = "Отмена"
    Finish = "Завершить"

    ConnectionToFNSLost = "💥 Потеряно соединение с ФНС. Пожалуйста, попробуй, авторизоваться заново: /login."

    PayingFor = "Он(-а) платит за"

    AlreadyLogin = "✅ Вы уже авторизированны в ФНС. Введите /new_receipt, чтобы разделить чек."
