#!/usr/bin/env python3
# type: ignore

import sys
import os
sys.path[0] = f'{os.getcwd()}/..'

from typing import Callable, Iterable
from decimal import Decimal as dec
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database import *
from data.database_provider import *
from data.models import *
from services.users_service import *
from services.students_service import *
from services.instructors_service import *
from services.courses_service import *
from services.settings_service import *


db_session: Session | None = None


def main():
    from docopt import docopt 
    global db_session

    doc = f"""
Create the datamodel for the courseca's DB. By default, this script 
also populates the DB with dummy values for testing. This module also 
provides utilities to help test DB code during development.

Usage:
    {sys.argv[0]} [-c | -i] [-s]

Options:
    -c, --create-ddl-only        Create the data model ONLY. Don't populate it
                                 with any data
    -i, --initial-metadata-only  Create the data model and populate it ONLY with 
                                 initial metadata, like status values and 
                                 descriptions.
    -s, --leave-session-open     Don't explicitly close session before exiting.
"""
    args = docopt(doc)
    try:
        db_init(
            db_provider = SQLite(database = "courseca.db"),
            create_datamodel = True,
            populate_metadata = not args['--create-ddl-only'],
        )
        db_session = get_db_session()

        if not (args['--create-ddl-only'] or args['--initial-metadata-only']):
            populate_database()
    finally:
        if not args['--leave-session-open']:
            db_session.close()
#:

def populate_database():
    insert_external_auth_providers()
    insert_countries()
    insert_students()
    insert_external_logins()
    insert_testimonials()
    insert_expertises()
    insert_instructors()
    insert_categories()
    insert_subcategories()
    insert_languages()
    insert_courses()
    enroll_students()
#:

############################################################################
##
##      EXTERNAL AUTH PROVIDERS
##
############################################################################

def insert_external_auth_providers():
    insert_rows(
        label = 'EXTERNAL AUTH PROVIDERS',
        summary = lambda eap : f"Created external auth provider {eap.name} ('{eap.id}')",
        insert_function = accept_external_auth_provider,
        rows = (
            {
                'name': 'Google',
                'end_point_url': 'https://accounts.google.com/o/oauth2/auth',
                # 'end_point_url': 'https://accounts.google.com/.well-known/openid-configuration',
            },
        )
    )
#:

############################################################################
##
##      COUNTRIES
##
############################################################################

def insert_countries():
    insert_rows(
        label = 'COUNTRIES',
        summary = lambda country: f"Created country '{country.iso_code}'",
        insert_function = accept_country,
        rows = (
            {
                'iso_code' : 'AU',
                'name' : 'Australia',
                'official_name' : 'Commonwealth of Australia',
            },
            {
                'iso_code' : 'BR',
                'name' : 'Brazil',
                'official_name' : 'Federative Republic of Brazil',
            },
            {
                'iso_code': 'DE',
                'name': 'Germany',
                'official_name': 'Federal Republic of Germany',
            },
            {
                'name': 'Ireland',
                'iso_code': 'IE',
                'official_name': 'Republic of Ireland',
            },
            {
                'iso_code': 'NO',
                'name': 'Norway',
                'official_name': 'Kingdom of Norway',
            },
            {
                'iso_code': 'PT',
                'name': 'Portugal',
                'official_name': 'Portuguese Republic',
            },
        )
    )
#:

############################################################################
##
##      STUDENTS
##
############################################################################

def insert_students():
    insert_rows(
        label = 'STUDENTS',
        summary = lambda stud: f"Created student '{stud.fullname}' (id: {stud.user_id})",
        insert_function = create_student_account,
        rows = (
            {
                'fullname': 'Augusto Andrade',
                'email_addr': 'augusto.andrade.aug@gmail.com',
                'password': 'abc',
                'birth_date': date(1997, 10, 15),
                'address_line1': 'Lote 33 - 1o Esquerdo',
                'address_line2': 'Rua Pimenta da Cruz',
                'zip_code': '2200-033 Águeda',
                'country_iso_code': 'PT',
            },
            {
                'fullname': 'Avelino Américo',
                'email_addr': 'ave@mail.com',
                'password': 'abc',
                'birth_date': date(1977, 10, 15),
                'address_line1': 'Lote 21 - 4o Direito',
                'address_line2': 'Av. Da Esperança',
                'zip_code': '1010-100 Amarante',
                'country_iso_code': 'PT',
            },
            {
                'fullname': 'Anthony Anderson',
                'email_addr': 'ant@mail.com',
                'password': 'abc',
                'birth_date': date(1980, 3, 5),
                'address_line1': 'Freedom Boulevard 10',
                'zip_code': '11301 Dublin',
                'country_iso_code': 'IE',
            },
            {
                'fullname': 'Antônio Ataíde',
                'email_addr': 'anto@mail.com',
                'password': 'abc',
                'birth_date': date(1999, 1, 23),
                'address_line1': 'R. José Higino, 115 ',
                'address_line2': 'Tijuca - Rio de Janeiro',
                'zip_code': 'RJ 20520-200',
                'country_iso_code': 'BR',
            },
            {
                'fullname': 'Andreas Schumacher',
                'email_addr': 'and@mail.com',
                'password': 'abc',
                'birth_date': date(1989, 1, 23),
                'address_line1': 'Sorenfeldring 17G',
                'address_line2': '22359 Hamburg',
                'zip_code': 'RJ 20520-200',
                'country_iso_code': 'DE',
            },
            {
                'fullname': 'Lene Nystrøm',
                'email_addr': 'len@mail.com',
                'password': 'abc',
                'birth_date': date(1989, 1, 23),
                'address_line1': 'Tollbodgata 22',
                'address_line2': '22359 Tønsberg',
                'zip_code': '20520',
                'country_iso_code': 'NO',
            },
            {
                'fullname': 'Russell Dowd',
                'email_addr': 'rus@mail.com',
                'password': 'abc',
                'birth_date': date(1993, 2, 23),
                'address_line1': '31 Limpinwood Valley Rd',
                'address_line2': 'Limpinwood',
                'zip_code': 'NSW 2484',
                'country_iso_code': 'AU',
            },
        ),
    )
#:

############################################################################
##
##      EXTERNAL LOGINS
##
############################################################################

def insert_external_logins():
        insert_rows(
        label = 'EXTERNAL LOGINS',
        summary = lambda data: (
            f"Added external user id '{data.external_user_id}' for student '{data.user_id}'"
        ),
        insert_function = add_external_login,
        rows = (
            {
                'user': student('Augusto Andrade'),
                'external_provider_id': external_provider('Google').id,
                'external_user_id': '108481805106399484676',
            },
        )
    )
#:

############################################################################
##
##      TESTIMONIALS
##
############################################################################

def insert_testimonials():
    insert_rows(
        label = 'TESTIMONIALS',
        summary = lambda test: f"Created '{test.user_name}' testimonial ",
        insert_function = create_testimonial,
        rows = (
            {
                'user_id': student('Augusto Andrade').user_id,   # type: ignore
                'user_occupation': 'CEO & Founder',
                'text': 'Quidem odit voluptate, obcaecati, explicabo nobis corporis perspiciatis nihil doloremque eius omnis officia voluptates, facere saepe quas consequatur aliquam unde. Ab numquam reiciendis sequi.',
                'image_url': '201.jpg',
            },
            {
                'user_id': student('Avelino Américo').user_id,   # type: ignore
                'user_occupation': 'Designer',
                'text': 'Export tempor illum tamen malis malis eram quae irure esse labore quem cillum quid cillum eram malis quorum velit fore eram velit sunt aliqua noster fugiat irure amet legam anim culpa.',
                'image_url': '202.jpg',
            },
            {
                'user_id': student('Anthony Anderson').user_id,   # type: ignore
                'user_occupation': 'Store Owner',
                'text': 'Enim nisi quem export duis labore cillum quae magna enim sint quorum nulla quem veniam duis minim tempor labore quem eram duis noster aute amet eram fore quis sint minim.',
                'image_url': '203.jpg',
            },
            {
                'user_id': student('Antônio Ataíde').user_id,   # type: ignore
                'user_occupation': 'Freelancer',
                'text': 'Fugiat enim eram quae cillum dolore dolor amet nulla culpa multos export minim fugiat minim velit minim dolor enim duis veniam ipsum anim magna sunt elit fore quem dolore labore illum veniam.',
                'image_url': '204.jpg',
            },
            {
                'user_id': student('Andreas Schumacher').user_id,   # type: ignore
                'user_occupation': 'Entrepreneur',
                'text': 'Quis quorum aliqua sint quem legam fore sunt eram irure aliqua veniam tempor noster veniam enim culpa labore duis sunt culpa nulla illum cillum fugiat legam esse veniam culpa fore nisi cillum quid.',
                'image_url': '205.jpg',
            },
        )
    )
#:

############################################################################
##
##      EXPERTISES
##
############################################################################

def insert_expertises():
    insert_rows(
        label = 'EXPERTISES',
        summary = lambda exp: f"Created expertise '{exp.name}' (id: '{exp.id}')",
        insert_function = create_expertise,
        rows = (
            {
                'name': 'Programação Web',
            },
            {
                'name': 'Segurança Informática',
            },
            {
                'name': 'Redes de Computadores',
            },
            {
                'name': 'Marketing',
            },
            {
                'name': 'Gestão', 
            },
            {
                'name': 'Programação de Sistemas',
            },
            {
                'name': 'Electrónica',
            },
            {
                'name': 'Desporto',
            },
            {
                'name': 'Turismo',
            },
        )
    )
#:

############################################################################
##
##      INSTRUCTORS
##
############################################################################

def insert_instructors():
    insert_rows(
        label = 'INSTRUCTORS',
        summary = lambda inst: f"Created instructor '{inst.fullname}' (id: '{inst.user_id}')",
        insert_function = create_instructor_account,
        rows = (
            {
                'fullname': 'Fernando Ferreira',
                'email_addr': 'fer@mail.com',
                'password': 'abc',
                'birth_date': date(1985, 1, 1),
                'address_line1': 'Urbanização das Flores Prédio A',
                'zip_code': '2200-011 Fátima',
                'country_iso_code': 'PT',
                'expertise_id': expertise('Programação Web').id,
                'presentation': 'Magni qui quod omnis unde et eos fuga et exercitationem. Odio veritatis perspiciatis quaerat qui aut aut aut',
                'presentation_image_url': '1001.jpg',
                'twitter_addr': 'https://twitter.com/fernanda_ferreira',
                'facebook_addr': 'https://facebook.com/fernandaferreira',
                'instagram_addr': 'https://instagram.com/fernerreira',
                'linkedin_addr': 'https://linkedin.com/prof_fernanda',
                'address_line2': '',
            },
            {
                'fullname': 'Francisca Fernandes',
                'email_addr': 'fra@mail.com',
                'password': 'abc',
                'birth_date': date(1984, 3, 1),
                'address_line1': 'Avenida de França N. 14',
                'zip_code': '1200-011 Fundão',
                'country_iso_code': 'PT',
                'expertise_id': expertise('Marketing').id,
                'presentation': 'Repellat fugiat adipisci nemo illum nesciunt voluptas repellendus. In architecto rerum rerum temporibus',
                'presentation_image_url': '1002.jpg',
                'twitter_addr': 'https://twitter.com/francisca_fernandes',
                'facebook_addr': 'https://facebook.com/franciscafernandes',
                'instagram_addr': 'https://instagram.com/franandes',
                'linkedin_addr': 'https://linkedin.com/prof_francisca',
                'address_line2': '',
            },
            {
                'fullname': 'Filipe Fontes',
                'email_addr': 'fil@mail.com',
                'password': 'abc',
                'birth_date': date(1989, 8, 24),
                'address_line1': 'Rua das Forças Armadas, 45',
                'zip_code': '1005-178 Felgueiras',
                'country_iso_code': 'PT',
                'expertise_id': expertise('Gestão').id,
                'presentation': 'Voluptas necessitatibus occaecati quia. Earum totam consequuntur qui porro et laborum toro des clara.',
                'presentation_image_url': '1003.jpg',
                'twitter_addr': 'https://twitter.com/filipe_fontes',
                'facebook_addr': 'https://facebook.com/filipefontes',
                'instagram_addr': 'https://instagram.com/filontes',
                'linkedin_addr': 'https://linkedin.com/prof_filipe',
                'address_line2': '',
            },
            {
                'fullname': 'Pedro Pereira',
                'email_addr': 'ped@mail.com',
                'password': 'abc',
                'birth_date': date(1987, 10, 19),
                'address_line1': 'Urbanização Pessoa, Lote 11120 20A',
                'zip_code': '2700-078 Porto',
                'country_iso_code': 'PT',
                'expertise_id': expertise('Programação de Sistemas').id,
                'presentation': 'Quidem odit voluptate, obcaecati, explicabo nobis corporis perspiciatis nihil. Necessitatibus occaecati quia.',
                'presentation_image_url': '1004.jpg',
                'twitter_addr': 'https://twitter.com/pedro_pereira',
                'facebook_addr': 'https://facebook.com/pedropereira',
                'instagram_addr': 'https://instagram.com/pedira',
                'linkedin_addr': 'https://linkedin.com/prof_pedro',
                'address_line2': '',
            },
            {
                'fullname': 'Roberta Rocha',
                'email_addr': 'rob@mail.com',
                'password': 'abc',
                'birth_date': date(1982, 12, 2),
                'address_line1': 'Praça da Resistência, Prédio 1',
                'zip_code': '3001-178 Rio Maior',
                'country_iso_code': 'PT',
                'expertise_id': expertise('Electrónica').id,
                'presentation': 'Earum totam consequuntur qui porro et laborum toro des clara. Voluptas necessitatibus occaecati quia. ',
                'presentation_image_url': '1005.jpg',
                'twitter_addr': 'https://twitter.com/roberta_rodrigues',
                'facebook_addr': 'https://facebook.com/robertarodrigues',
                'instagram_addr': 'https://instagram.com/robegues',
                'linkedin_addr': 'https://linkedin.com/prof_roberta',
                'address_line2': '',
            },
            {
                'fullname': 'Carlos Coelho',
                'email_addr': 'car@mail.com',
                'password': 'abc',
                'birth_date': date(1978, 5, 14),
                'address_line1': 'Calçada de Coimbra, Lote 16',
                'zip_code': '2441-374 Condeixa',
                'country_iso_code': 'PT',
                'expertise_id': expertise('Desporto').id,
                'presentation': 'Sint culpa placeat nulla error commodi impedit vitae facere mollitia nesciunt, aliquam ipsum consequuntur quas harum nobis.',
                'presentation_image_url': '1006.jpg',
                'twitter_addr': 'https://twitter.com/carlos_coelho',
                'facebook_addr': 'https://facebook.com/carloscoelho',
                'instagram_addr': 'https://instagram.com/carcoe',
                'linkedin_addr': 'https://linkedin.com/prof_carlos',
                'address_line2': '',
            },
            {
                'fullname': 'Rui Rodrigues',
                'email_addr': 'rui@mail.com',
                'password': 'abc',
                'birth_date': date(1983, 7, 24),
                'address_line1': 'Rua da Rotunda, n. 6',
                'zip_code': '3001-167 Rio Maior',
                'country_iso_code': 'PT',
                'expertise_id': expertise('Turismo').id,
                'presentation': 'Possimus facilis dolor minus quia qui esse laborum distinctio. Ipsum, quaerat! ',
                'presentation_image_url': '1007.jpg',
                'twitter_addr': 'https://twitter.com/rui_rodrigues',
                'facebook_addr': 'https://facebook.com/ruirodrigues',
                'instagram_addr': 'https://instagram.com/rugues',
                'linkedin_addr': 'https://linkedin.com/prof_rui',
                'address_line2': '',
            },
        ),
    )
#:

############################################################################
##
##      CATEGORIES
##
############################################################################

def insert_categories():
    insert_rows(
        label = 'CATEGORIES',
        summary = lambda category: f"Created category '{category.name}' (id: '{category.id}')",
        insert_function = create_category,
        rows = (
            {
                'name': 'Gestão',
                'description': 'Gestão de empresas, pública, internacional, MBAs, etc.',
            },
            {
                'name': 'Marketing & Publicidade',
                'description': 'Marketing, publicidade, anúncios, promoções, eventos, campanhas.',
            },
            {
                'name': 'Programação & Desenvolvimento de Software',
                'description': 'Programação, desenvolvimento, engenharia de software, linguagens de programação, etc.',
            },
            {
                'name': 'Electrónica',
                'description': 'Fundamentos da electrónica, electrónica aplicada, circuitos integrados, etc.',
            },
            {
                'name': 'Hotelaria e Turismo',
                'description': 'Todos os aspectos relacionados com turismo, hotelaria, alojamento e restauração.',
            },
            {
                'name': 'Desporto',
                'description': 'Futebol, atletismo, hóquei, e outras modalidades.',
            },
        )
    )
#:

############################################################################
##
##      SUBCATEGORIES
##
############################################################################

def insert_subcategories():
    insert_rows(
        label = 'SUBCATEGORIES',
        summary = lambda subcategory: f"Created subcategory '{subcategory.name}' (id: '{subcategory.id}')",
        insert_function = create_subcategory,
        rows = (
            {
                'name': 'Gestão Pública',
                'description': 'Gestão de entidades e institutos do sector público.',
                'category_id': cat('Gestão').id,
            },
            {
                'name': 'Contabilidade & Finanças',
                'description': 'Contabilidade e finanças para o sector empresarial e público.',
                'category_id': cat('Gestão').id,
            },
            {
                'name': 'Marketing Web',
                'description': 'Conceitos, técnicas e estratégias de marketing para sites e aplicações Web.',
                'category_id': cat('Marketing & Publicidade').id,
            },
            {
                'name': 'Campanhas de Marketing',
                'description': 'Desenvolvimento e implementação de campanhas de marketing.',
                'category_id': cat('Marketing & Publicidade').id,
            },
            {
                'name': 'Programação em C++',
                'description': 'Programação na linguagem C++. Abrange C++ moderno e legado.',
                'category_id': cat('Programação & Desenvolvimento de Software').id,
            },
            {
                'name': 'Programação Web',
                'description': 'Desenvolvimento de sites e aplicações Web.',
                'category_id': cat('Programação & Desenvolvimento de Software').id,
            },
            {
                'name': 'Programação de Sistemas',
                'description': 'Programação de baixo-nível de sistemas operativos, redes, device driverts, etc.',
                'category_id': cat('Programação & Desenvolvimento de Software').id,
            },
            {
                'name': 'Soldadura',
                'description': 'Soldadura e micro-soldadura de componentes electrónicos.',
                'category_id': cat('Electrónica').id,
            },
            {
                'name': 'Sistemas Digitais',
                'description': 'Portas lógicas, microcontroladores, unidades de memória.',
                'category_id': cat('Electrónica').id,
            },
            {
                'name': 'Gestão Túristica',
                'description': 'Gestão de empresas túristicas ou de áreas relacionadas.',
                'category_id': cat('Hotelaria e Turismo').id,
            },
            {
                'name': 'Desporto & Aventura',
                'description': 'Actividades e eventos túristicos relacionados com desporto.',
                'category_id': cat('Hotelaria e Turismo').id,
            },
            {
                'name': 'Natação',
                'description': 'Cursos sobre natação.',
                'category_id': cat('Desporto').id,
            },
            {
                'name': 'Arbitragem - Futebol',
                'description': 'Cursos sobre arbitragem para futebol.',
                'category_id': cat('Desporto').id,
            },
        ),
    )
#:

############################################################################
##
##      LANGUAGES
##
############################################################################

def insert_languages():
    insert_rows(
        label = 'LANGUAGES',
        summary = lambda language: f"Created language '{language.name}' (id: '{language.iso_code}')",
        insert_function = accept_language,
        rows = (
            {
                'iso_code': 'pt',
                'name': 'Português',
            },
            {
                'iso_code': 'en',
                'name': 'English',
            },
            {
                'iso_code': 'es',
                'name': 'Español',
            },
        )
    )
#:

############################################################################
##
##      COURSES
##
############################################################################

def insert_courses():
    insert_rows(
        label = 'COURSES',
        summary = lambda course: f"Created course '{course.title}' (id: '{course.id}')",
        insert_function = create_course,
        rows = (
            {
                'title': 'Gestão Pública - Introdução',
                'summary': 'Lorem ipsum dolor sit amet consectetur adipisicing elit. Suscipit perferendis praesentium nobis accusamus.',
                'description': 'Fugit, ipsum illum temporibus perspiciatis labore perferendis? Dolorum repudiandae soluta animi placeat laborum ducimus, optio sequi beatae. Assumenda expedita a dolore quod. Doloremque vitae, explicabo dicta, dolor quae veniam, facilis magni aperiam consectetur quidem impedit molestias. Neque optio labore ipsa at explicabo repudiandae voluptatem deserunt dicta ducimus facere!  Hic libero at iure laboriosam aliquid deleniti quod assumenda saepe doloremque! Architecto ratione inventore nam soluta quibusdam in tempore nostrum omnis rerum facere officia quae, corrupti veniam maxime, ea iste aliquid, dolores saepe quidem.',
                'main_image_url': '3001.jpg',
                'subcategory_id': subcat('Gestão Pública').id,
                'instructor_id': instructor('Filipe Fontes').user_id,
                'language_id': 'pt',
                'price': dec(200),
            },
            {
                'title': 'SEO - Optimizações Motores de Busca',
                'summary': 'Et architecto provident deleniti facere repellat nobis iste. Id facere quia quae dolores dolorem tempore.',
                'description': 'Error iure facere incidunt minima dolorum adipisci culpa! Maiores velit doloribus perferendis tempore, dicta est, sit necessitatibus commodi, sapiente minus quas. Vitae repellat quasi sunt, iusto atque pariatur! Suscipit sed maxime quaerat obcaecati accusamus neque nobis quidem, quisquam ducimus nemo illo corporis fugit eaque fugiat nisi, dolorum minima dignissimos, enim deserunt sint corrupti? Voluptas magnam molestias modi ea, sunt id nemo amet reiciendis at iusto iure nam, quas dolor tempora quo nihil voluptatem impedit harum mollitia.',
                'main_image_url': '3002.jpg',
                'subcategory_id': subcat('Marketing Web').id,
                'instructor_id': instructor('Francisca Fernandes').user_id,
                'language_id': 'pt',
                'price': dec(330),
            },
            {
                'title': 'Épocas de Saldos e Promoções',
                'summary': 'Maiores velit doloribus perferendis tempore, dicta est, sit necessitatibus commodi, sapiente minus quas. ',
                'description': 'Consectetur dicta fuga, fugiat veniam hic autem in cupiditate, non impedit nostrum porro! Corrupti aspernatur incidunt aliquam earum quis fugit soluta ad perspiciatis culpa eius dignissimos corporis vel optio recusandae, ipsum ullam libero id, ex harum cumque unde eveniet natus! Laboriosam voluptatem vel nemo facere non quidem officia, consequatur tenetur doloremque labore dolorum, corrupti dolore tempora ducimus! Fugit, ipsum illum temporibus perspiciatis labore perferendis? ',
                'main_image_url': '3003.jpg',
                'subcategory_id': subcat('Campanhas de Marketing').id,
                'instructor_id': instructor('Filipe Fontes').user_id,
                'language_id': 'pt',
                'price': dec(0),
            },
            {
                'title': 'Estruturas de Dados em C++',
                'summary': 'Et architecto provident deleniti facere repellat nobis iste. Id facere quia quae dolores dolorem tempore.',
                'description': 'Corrupti omnis maxime voluptatem sed nobis illo dolorum corporis est laboriosam molestiae, consectetur necessitatibus nihil delectus ea ullam obcaecati magnam? Sequi quis quae voluptates rerum obcaecati modi, qui molestias sit soluta recusandae aliquid non libero voluptas ipsam dicta numquam explicabo reprehenderit animi alias totam illo autem laborum a. Corrupti nam dicta, debitis et consequatur, explicabo distinctio incidunt cumque ab ullam eum sequi? Culpa?',
                'main_image_url': '3004.jpg',
                'subcategory_id': subcat('Programação em C++').id,
                'instructor_id': instructor('Pedro Pereira').user_id,
                'language_id': 'pt',
                'price': dec(250),
            },
            {
                'title': 'Desenvolvimento de Websites',
                'summary': 'Consectetur et, temporibus velit inventore porro sint dolore hic veniam sapiente, quos voluptatem aliquid, explicabo doloremque sunt!',
                'description': 'Possimus obcaecati, cumque perferendis praesentium neque est eligendi voluptatum accusantium maiores blanditiis, at minima aliquid labore alias corrupti a iusto accusamus. Et iste est eos, eligendi explicabo quae illum nesciunt quis laborum, cumque mollitia dignissimos labore nisi laudantium accusamus modi eveniet ex itaque aliquam tenetur, maiores laboriosam. Ipsam, iusto! Nesciunt, impedit reiciendis. Repudiandae harum iste libero non reprehenderit hic distinctio maxime esse repellendus, tempora at cupiditate qui nulla numquam! Fugit, saepe.',
                'main_image_url': '3005.jpg',
                'subcategory_id': subcat('Programação Web').id,
                'instructor_id': instructor('Fernando Ferreira').user_id,
                'language_id': 'pt',
                'price': dec(350),
            },
            {
                'title': 'Programação de Device Drivers',
                'summary': 'Ex voluptatibus amet magnam maxime. Repellat quis eos laudantium magnam alias quisquam repellendus magni, quas nam vitae explicabo sed necessitatibus? Eaque!',
                'description': 'Soluta repellendus odit est quo a at unde iure dolore, eligendi harum sint voluptas quam error atque quis laudantium eaque, beatae sunt hic commodi dicta dolor nulla corporis veritatis! Optio tenetur quae sit labore. Fugiat, sed ad voluptatem doloribus architecto, tempora, consequuntur reprehenderit explicabo dignissimos est magnam voluptate consectetur ducimus at. Vitae vero reiciendis cumque aut neque similique officiis delectus obcaecati sint odio?',
                'main_image_url': '3006.jpg',
                'subcategory_id': subcat('Programação de Sistemas').id,
                'instructor_id': instructor('Fernando Ferreira').user_id,
                'language_id': 'pt',
                'price': dec(550),
            },
            {
                'title': 'Microsoldadura de SMD',
                'summary': 'Esse est nemo dolorum tempora numquam dolorem in optio sed quasi voluptate! Voluptatibus animi accusantium ad! Ratione et possimus repellendus vero nemo id modi.',
                'description': 'Incidunt vero deserunt explicabo sequi perferendis. Sint, sed. Explicabo blanditiis, sunt nesciunt delectus aperiam amet dignissimos exercitationem consequuntur soluta modi dolores a placeat qui corrupti ducimus. Esse, suscipit illum natus distinctio, sint repellendus quod expedita eveniet facere consequatur quas optio corrupti ratione non veniam deleniti dolor? Repudiandae harum iste libero non reprehenderit hic distinctio maxime esse repellendus, tempora at cupiditate qui nulla numquam! Fugit, saepe.',
                'main_image_url': '3007.jpg',
                'subcategory_id': subcat('Soldadura').id,
                'instructor_id': instructor('Roberta Rocha').user_id,
                'language_id': 'pt',
                'price': dec(550),
            },
            {
                'title': 'Gestor Turístico',
                'summary': 'Et architecto provident deleniti facere repellat nobis iste. Id facere quia quae dolores dolorem tempore.',
                'description': 'Non rem numquam debitis obcaecati unde repellendus, eaque eum est saepe accusamus molestias ipsa. Consectetur dicta fuga, fugiat veniam hic autem in cupiditate, non impedit nostrum porro! Corrupti aspernatur incidunt aliquam earum quis fugit soluta ad perspiciatis culpa eius dignissimos corporis vel optio recusandae, ipsum ullam libero id, ex harum cumque unde eveniet natus! Laboriosam voluptatem vel nemo facere non quidem officia, consequatur tenetur doloremque labore dolorum, corrupti dolore tempora ducimus!',
                'main_image_url': '3008.jpg',
                'subcategory_id': subcat('Gestão Túristica').id,
                'instructor_id': instructor('Filipe Fontes').user_id,
                'language_id': 'pt',
                'price': dec(189),
            },
            {
                'title': 'Estilo Borboleta',
                'summary': 'Id facere quia quae dolores dolorem tempore. Et architecto provident deleniti facere repellat nobis iste.',
                'description': 'Lorem ipsum dolor sit amet consectetur adipisicing elit. Ut ab deserunt et vitae sunt, enim dolores beatae esse necessitatibus iusto. Error iure facere incidunt minima dolorum adipisci culpa! Maiores velit doloribus perferendis tempore, dicta est, sit necessitatibus commodi, sapiente minus quas. Vitae repellat quasi sunt, iusto atque pariatur! Suscipit sed maxime quaerat obcaecati accusamus neque nobis quidem, quisquam ducimus nemo illo corporis fugit eaque fugiat nisi, dolorum minima dignissimos, enim deserunt sint corrupti?',
                'main_image_url': '3009.jpg',
                'subcategory_id': subcat('Natação').id,
                'instructor_id': instructor('Filipe Fontes').user_id,
                'language_id': 'pt',
                'price': dec(149),
            },
            {
                'title': 'Arbitragem com VAR e Sistemas de Apoio',
                'summary': 'Necessitatibus corporis quos, obcaecati iste quae minima culpa architecto, voluptatum rem perferendis praesentium!',
                'description': 'Nobis expedita doloribus optio rem! Assumenda illum, cumque laboriosam esse blanditiis veniam dolor rem, dignissimos reiciendis odit suscipit mollitia nemo consequuntur eaque quae tenetur vero? Sint ipsum repudiandae, nobis consequuntur nesciunt vitae rem excepturi labore eveniet quasi aliquam, consequatur voluptas totam magnam quaerat libero atque recusandae iure. Aliquid itaque maiores adipisci quod unde voluptate deleniti iste praesentium explicabo nam fugiat iusto, soluta, est quas earum nisi libero rerum veritatis nesciunt?',
                'main_image_url': '3010.jpg',
                'subcategory_id': subcat('Arbitragem - Futebol').id,
                'instructor_id': instructor('Carlos Coelho').user_id,
                'language_id': 'pt',
                'price': dec(279),
            },
        ),
    )
#:

############################################################################
##
##      ENROLLMENTS
##
############################################################################

def enroll_students():
    new_line_after = 5
    counter = 0
    def summary(enroll: Enrollment):
        nonlocal counter, new_line_after
        student_name = get_user_by_id(enroll.student_id, db_session, ).firstname
        course_title = get_course_by_id(enroll.course_id, db_session).title
        msg = f"Enrolled student '{student_name}' in course '{course_title}'"
        if (counter := counter + 1) == new_line_after:
            msg += '\n'
            counter = 0
        return msg
    #:

    insert_rows(
        insert_function = enroll_student_in_course,
        label = 'ENROLLMENTS',
        summary = summary,
        rows = (
            {
                'student': student('Augusto Andrade'),
                'course': course('Gestão Pública - Introdução'),
            },
            {
                'student': student('Augusto Andrade'),
                'course': course('SEO - Optimizações Motores de Busca'),
            },
            {
                'student': student('Augusto Andrade'),
                'course': course('Arbitragem com VAR e Sistemas de Apoio'),
            },
            {
                'student': student('Augusto Andrade'),
                'course': course('Épocas de Saldos e Promoções'),
            },
            {
                'student': student('Augusto Andrade'),
                'course': course('Desenvolvimento de Websites'),
            },

            {
                'student': student('Avelino Américo'),
                'course': course('Gestão Pública - Introdução'),
            },
            {
                'student': student('Avelino Américo'),
                'course': course('Microsoldadura de SMD'),
            },
            {
                'student': student('Avelino Américo'),
                'course': course('Desenvolvimento de Websites'),
            },
            {
                'student': student('Avelino Américo'),
                'course': course('Épocas de Saldos e Promoções'),
            },
            {
                'student': student('Avelino Américo'),
                'course': course('SEO - Optimizações Motores de Busca'),
            },

            {
                'student': student('Antônio Ataíde'),
                'course': course('Épocas de Saldos e Promoções'),
            },
            {
                'student': student('Antônio Ataíde'),
                'course': course('SEO - Optimizações Motores de Busca'),
            },
            {
                'student': student('Antônio Ataíde'),
                'course': course('Estilo Borboleta'),
            },
            {
                'student': student('Antônio Ataíde'),
                'course': course('Desenvolvimento de Websites'),
            },
            {
                'student': student('Antônio Ataíde'),
                'course': course('Gestor Turístico'),
            },

            {
                'student': student('Anthony Anderson'),
                'course': course('SEO - Optimizações Motores de Busca'),
            },
            {
                'student': student('Anthony Anderson'),
                'course': course('Gestor Turístico'),
            },
            {
                'student': student('Anthony Anderson'),
                'course': course('Arbitragem com VAR e Sistemas de Apoio'),
            },
            {
                'student': student('Anthony Anderson'),
                'course': course('Épocas de Saldos e Promoções'),
            },
            {
                'student': student('Anthony Anderson'),
                'course': course('Desenvolvimento de Websites'),
            },

            {
                'student': student('Andreas Schumacher'),
                'course': course('SEO - Optimizações Motores de Busca'),
            },
            {
                'student': student('Andreas Schumacher'),
                'course': course('Gestão Pública - Introdução'),
            },
            {
                'student': student('Andreas Schumacher'),
                'course': course('Arbitragem com VAR e Sistemas de Apoio'),
            },
            {
                'student': student('Andreas Schumacher'),
                'course': course('Desenvolvimento de Websites'),
            },
            {
                'student': student('Andreas Schumacher'),
                'course': course('Programação de Device Drivers'),
            },

            {
                'student': student('Lene Nystrøm'),
                'course': course('Programação de Device Drivers'),
            },
            {
                'student': student('Lene Nystrøm'),
                'course': course('Estruturas de Dados em C++'),
            },
            {
                'student': student('Lene Nystrøm'),
                'course': course('Estilo Borboleta'),
            },
            {
                'student': student('Lene Nystrøm'),
                'course': course('Desenvolvimento de Websites'),
            },
            {
                'student': student('Lene Nystrøm'),
                'course': course('SEO - Optimizações Motores de Busca'),
            },

            {
                'student': student('Russell Dowd'),
                'course': course('Programação de Device Drivers'),
            },
            {
                'student': student('Russell Dowd'),
                'course': course('Estruturas de Dados em C++'),
            },
            {
                'student': student('Russell Dowd'),
                'course': course('SEO - Optimizações Motores de Busca'),
            },
            {
                'student': student('Russell Dowd'),
                'course': course('Microsoldadura de SMD'),
            },
            {
                'student': student('Russell Dowd'),
                'course': course('Desenvolvimento de Websites'),
            },
        )
    )
#:

############################################################################
##
##      HELPER FUNCTIONS
##
############################################################################

def insert_rows(
        insert_function: Callable,
        label: str,
        rows: Iterable,
        summary: Callable | None = None,
):
    print()
    print(f"{label} _____________________________________________________")

    for row in rows:
        row['db_session'] = db_session
        obj = insert_function(**row)
        if summary:
            print(f"[+] {summary(obj)}")
#:

def external_provider(name: str):
    return make_simple_query(ExternalProvider, ExternalProvider.name == name)
#:

def student(fullname: str):
    return make_simple_query(Student, Student.fullname == fullname)
#:

def expertise(name: str):
    return make_simple_query(InstructorExpertise, InstructorExpertise.name == name)
#:

def instructor(fullname: str):
    return make_simple_query(Instructor, Instructor.fullname == fullname)
#:

def cat(name: str):
    return make_simple_query(Category, Category.name == name)
#:

def subcat(name: str) -> SubCategory:
    return make_simple_query(SubCategory, SubCategory.name == name)
#:

def course(title: str) -> Course:
    return make_simple_query(Course, Course.title == title)
#:

def make_simple_query(table, query_fn):
    select_stmt = select(table).where(query_fn)
    return db_session.execute(select_stmt).scalar_one()
#:

if __name__ == '__main__':
    main()
#:
