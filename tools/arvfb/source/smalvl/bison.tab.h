/* A Bison parser, made by GNU Bison 3.0.2.  */

/* Bison interface for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2013 Free Software Foundation, Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.  */

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

#ifndef YY_YY_BISON_TAB_H_INCLUDED
# define YY_YY_BISON_TAB_H_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 1
#endif
#if YYDEBUG
extern int yydebug;
#endif

/* Token type.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    FUNCTION = 258,
    VAR_BEGIN = 259,
    ARRAY_DECLARATION = 260,
    IDENTIFIER = 261,
    NUMBER = 262,
    STRING_DEFINITION = 263,
    END_INSTRUCTION = 264,
    ARG_SPLITTER = 265,
    PLUS = 266,
    MINUS = 267,
    DIVIDE = 268,
    MULTIPLY = 269,
    DIVIDE_MOD = 270,
    ASSIGN = 271,
    MORE = 272,
    LESS = 273,
    MORE_OR_EQUAL = 274,
    LESS_OR_EQUAL = 275,
    EQUAL = 276,
    NOT_EQUAL = 277,
    OPEN_BLOCK = 278,
    CLOSE_BLOCK = 279,
    OPEN_BRACKET = 280,
    CLOSE_BRACKET = 281,
    STRING_CONCETATE = 282,
    RETURN = 283,
    INCLUDE = 284,
    REQUIRE = 285,
    OPEN_SQUARE_BRACKET = 286,
    CLOSE_SQUARE_BRACKET = 287,
    IF = 288,
    ELSE = 289,
    TRUE = 290,
    FALSE = 291,
    INC = 292,
    DEC = 293,
    WHILE = 294,
    FOR = 295,
    BREAK = 296,
    UNSET = 297,
    DEVIDE = 298
  };
#endif

/* Value type.  */


extern YYSTYPE yylval;

int yyparse (void);

#endif /* !YY_YY_BISON_TAB_H_INCLUDED  */
