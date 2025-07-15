curl -LsSf https://astral.sh/uv/install.sh | sh
. $HOME/.local/bin/env
make install

echo ">>> Начинаю загрузку database.sql"
psql -a -d $DATABASE_URL -f database.sql
echo ">>> Загрузка database.sql завершена"