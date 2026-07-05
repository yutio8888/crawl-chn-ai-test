/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison interface for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015, 2018-2021 Free Software Foundation,
   Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

#ifndef YY_YY_LEVCOMP_TAB_HH_INCLUDED
# define YY_YY_LEVCOMP_TAB_HH_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int yydebug;
#endif

/* Token kinds.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    YYEMPTY = -2,
    YYEOF = 0,                     /* "end of file"  */
    YYerror = 256,                 /* error  */
    YYUNDEF = 257,                 /* "invalid token"  */
    DEFAULT_DEPTH = 258,           /* DEFAULT_DEPTH  */
    SHUFFLE = 259,                 /* SHUFFLE  */
    CLEAR = 260,                   /* CLEAR  */
    SUBST = 261,                   /* SUBST  */
    TAGS = 262,                    /* TAGS  */
    KFEAT = 263,                   /* KFEAT  */
    KITEM = 264,                   /* KITEM  */
    KMONS = 265,                   /* KMONS  */
    KMASK = 266,                   /* KMASK  */
    KPROP = 267,                   /* KPROP  */
    NAME = 268,                    /* NAME  */
    DEPTH = 269,                   /* DEPTH  */
    ORIENT = 270,                  /* ORIENT  */
    PLACE = 271,                   /* PLACE  */
    CHANCE = 272,                  /* CHANCE  */
    WEIGHT = 273,                  /* WEIGHT  */
    MONS = 274,                    /* MONS  */
    ITEM = 275,                    /* ITEM  */
    MARKER = 276,                  /* MARKER  */
    COLOUR = 277,                  /* COLOUR  */
    PRELUDE = 278,                 /* PRELUDE  */
    MAIN = 279,                    /* MAIN  */
    VALIDATE = 280,                /* VALIDATE  */
    VETO = 281,                    /* VETO  */
    EPILOGUE = 282,                /* EPILOGUE  */
    NSUBST = 283,                  /* NSUBST  */
    WELCOME = 284,                 /* WELCOME  */
    LFLOORCOL = 285,               /* LFLOORCOL  */
    LROCKCOL = 286,                /* LROCKCOL  */
    LFLOORTILE = 287,              /* LFLOORTILE  */
    LROCKTILE = 288,               /* LROCKTILE  */
    FTILE = 289,                   /* FTILE  */
    RTILE = 290,                   /* RTILE  */
    TILE = 291,                    /* TILE  */
    SUBVAULT = 292,                /* SUBVAULT  */
    FHEIGHT = 293,                 /* FHEIGHT  */
    DESC = 294,                    /* DESC  */
    ORDER = 295,                   /* ORDER  */
    COMMA = 296,                   /* COMMA  */
    COLON = 297,                   /* COLON  */
    PERC = 298,                    /* PERC  */
    DASH = 299,                    /* DASH  */
    CHARACTER = 300,               /* CHARACTER  */
    NUMBER = 301,                  /* NUMBER  */
    STRING = 302,                  /* STRING  */
    MAP_LINE = 303,                /* MAP_LINE  */
    MONSTER_NAME = 304,            /* MONSTER_NAME  */
    ITEM_INFO = 305,               /* ITEM_INFO  */
    LUA_LINE = 306                 /* LUA_LINE  */
  };
  typedef enum yytokentype yytoken_kind_t;
#endif

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
union YYSTYPE
{
#line 36 "levcomp.ypp"

    int i;
    double f;
    const char *text;

#line 121 "levcomp.tab.hh"

};
typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif


extern YYSTYPE yylval;


int yyparse (void);


#endif /* !YY_YY_LEVCOMP_TAB_HH_INCLUDED  */
