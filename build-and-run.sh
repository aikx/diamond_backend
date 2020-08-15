function lg_info {
    dt=$(date +"[%m-%d %H:%M:%S]")
    echo "=> ${dt} $1"
}


if [ "${DJ_CONDA_ENV}" ]
then
  dj_name=${DJ_CONDA_ENV}
else
  dj_name="dj"
fi
source activate "${dj_name}"


django_proj_root="Dia"
lg_info "venv \`${dj_name}\` activated, rm caches..."
find . -name 'migrations' -type d -exec rm -rf {} +
find . -name '__pycache__' -type d -exec rm -rf {} +

rm -rf "${django_proj_root}/**/migrations"
rm -rf "${django_proj_root}/**/migrations/*"
rm -rf "${django_proj_root}/**/migrations/00*"
rm -rf "${django_proj_root}/**/__pycache__"


cd "${django_proj_root}" || exit
django_proj_root=$(pwd)
lg_dir="logging"
if [ ! -d "${lg_dir}" ]
then
  lg_info "mk log dir \`${lg_dir}\`"
  mkdir "${lg_dir}"
fi

lg_file="${lg_dir}/run.sh.log"
:> "${lg_file}"
lg_info "caches removed, auto-make migs... (outputs are redirected to \`${lg_file}\`)"
for app_dir in $(find . -name views.py)''
do
  cd "$(dirname "${app_dir}")" || exit
  pack=${PWD##*/}
  cd "${django_proj_root}" || exit
  python manage.py makemigrations "${pack}" >> "${lg_file}"
  lg_info "app \`${pack}\` detected, auto-make migs..."
done
python manage.py migrate >> "${lg_file}"


lg_info "db migrated, check log files..."

lg_file="${lg_dir}/console.log"
if [ ! -f "${lg_file}" ]
then
  lg_info "create log file \`${lg_file}\`"
  touch "${lg_file}"
fi

lg_file="${lg_dir}/error.log"
if [ ! -f "${lg_file}" ]
then
  lg_info "create log file \`${lg_file}\`"
  touch "${lg_file}"
fi


lg_info "log files checked, run server..."
if [ "$1" ]
then
  mode="shell"
else
  mode="runserver"
fi
python manage.py "${mode}"


lg_info "server exited"
