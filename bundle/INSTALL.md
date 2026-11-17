# ACadHotKey — ручная установка для AutoCAD 2020–2024 (Windows x64)

Архив `ACadHotKey-manual-install-v<версия>.zip` содержит готовый пакет.
Сборка исходников, инсталлятор и права администратора не нужны.
Все устанавливаемые файлы находятся только в профиле текущего пользователя (`%APPDATA%`).

## Установка

1. Закройте все экземпляры AutoCAD. Если раньше устанавливали другую копию ACadHotKey,
   удалите её из прежнего места автозагрузки, чтобы не загружались две копии.
2. В свойствах скачанного ZIP включите «Разблокировать», если этот флажок есть, затем распакуйте архив
   в любую временную папку. Рядом с этой инструкцией должна находиться папка `ACadHotKey.bundle`.
3. Нажмите `Win+R`, введите `%APPDATA%\Autodesk\ApplicationPlugins` и нажмите Enter.
   Если папки нет, создайте её в своём профиле.
4. Скопируйте туда **всю папку** `ACadHotKey.bundle`, сохранив имя и структуру:

   ```text
   %APPDATA%\Autodesk\ApplicationPlugins\ACadHotKey.bundle\
     PackageContents.xml
     Contents\2020\ACadHotKey.dll
     Contents\2020\ACadHotKey.Core.dll
     Contents\2020\ACadHotKey.config.xml
     Contents\2021-2024\ACadHotKey.dll
     Contents\2021-2024\ACadHotKey.Core.dll
     Contents\2021-2024\ACadHotKey.config.xml
   ```

   Не копируйте DLL по отдельности и не создавайте вторую вложенную папку `ACadHotKey.bundle`.
   Ничего не нужно копировать в `Program Files` или `ProgramData`.
5. Запустите AutoCAD 2020, 2021, 2022, 2023 или 2024. Пакет настроен на автоматическую загрузку:
   AutoCAD 2020 выбирает `Contents\2020` (.NET Framework 4.7),
   AutoCAD 2021–2024 — `Contents\2021-2024` (.NET Framework 4.8).
6. Выполните `ACHK_LIST` — появятся загруженные назначения. В области чертежа нажмите `1`
   для запуска `LINE`. `ACHK_OFF` выключает перехват, `ACHK_ON` включает его.

## Если пакет не загрузился

Проверьте путь к `PackageContents.xml` и наличие обеих DLL и XML в каждой папке.
Если [`APPAUTOLOAD`](https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-Core/files/GUID-33E75B9A-93AC-4FBF-B941-0F99A6AC3617.htm)
установлен в `0`, автоматическое обнаружение пакетов отключено;
верните обычное значение `14`, если это допускается настройками вашей организации, и перезапустите AutoCAD.
Если AutoCAD запрашивает разрешение на загрузку, разрешите загрузку ACadHotKey.
При блокировке `SECURELOAD` добавьте **папку сборки вашей версии** в `TRUSTEDPATHS`
(«Параметры» → «Файлы» → «Надёжные папки»), сохраняя проверку безопасности включённой:

```text
%APPDATA%\Autodesk\ApplicationPlugins\ACadHotKey.bundle\Contents\2020
%APPDATA%\Autodesk\ApplicationPlugins\ACadHotKey.bundle\Contents\2021-2024
```

Для диагностики можно загрузить `ACadHotKey.dll` своей версии через `NETLOAD`, затем выполнить
`ACHK_LIST`. Не выбирайте `ACadHotKey.Core.dll`. Если политика организации запрещает пользовательские
плагины, потребуется разрешение её администратора; архив не меняет эту политику.

## Настройки, обновление и удаление

Свои назначения храните отдельно: создайте `%APPDATA%\ACadHotKey`, скопируйте туда
`ACadHotKey.config.xml` из папки своей версии, измените назначения и выполните `ACHK_RELOAD`.
Этот файл имеет приоритет над XML внутри пакета и сохраняется при обновлении.

Для обновления закройте AutoCAD, удалите старую папку
`%APPDATA%\Autodesk\ApplicationPlugins\ACadHotKey.bundle` и скопируйте новую целиком.
Предварительно сохраните изменения, если редактировали XML непосредственно в пакете.

Для удаления закройте AutoCAD и удалите папку `ACadHotKey.bundle` из `ApplicationPlugins`.
При необходимости отдельно удалите свои настройки `%APPDATA%\ACadHotKey`.

Архив не содержит библиотек Autodesk: их предоставляет установленный AutoCAD.
AutoCAD LT и AutoCAD 2025+ в этот выпуск не входят.
