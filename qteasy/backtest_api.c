/* ====================================== */
/* File:     backtest_api.c
/* Author:   Jackie PENG
/* Contact:  jackie.pengzhao@gmail.com
/* Created:  2024-03-31
/* Desc:
/*   fast APIs developed in C for
/* backtesting in order to speed up the
/* process.
/* ====================================== */

/* ====================================== */
/* Headers */
/* ====================================== */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>

static PyObject *
spam_system(PyObject *self, PyObject *args)
{
    const char *command;
    int sts;

    if (!PyArg_ParseTuple(args, "s", &command))
        return NULL;
    sts = system(command);
    return PyLong_FromLong(sts);
}

PyMODINIT_FUNC
PyInit_spam(void)
{
    PyObject *m;

    m = PyModule_Create(&spammodule);
    if (m == NULL)
        return NULL;

    SpamError = PyErr_NewException("spam.error", NULL, NULL);
    Py_XINCREF(SpamError);
    if (PyModule_AddObject(m, "error", SpamError) < 0) {
        Py_XDECREF(SpamError);
        Py_CLEAR(SpamError);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}

static PyObject *SpamError;

static PyObject *
spam_divide(PyObject *self, PyObject *args)
{
    double a, b;
    if (!PyArg_ParseTuple(args, "dd", &a, &b))
        return NULL;
    if (b == 0)
    {
        PyErr_SetString(SpamError, "division by zero");
        return NULL;
    }
    return Py_BuildValue("d", a / b);
}

static PyObject *
spam_system(PyObject *self, PyObject *args)
{
    const char *command;
    int sts;
    if (!PyArg_ParseTuple(args, "s", &command))
        return NULL;
    sts = system(command);
    if (sts < 0)
    {
        PyErr_SetString(SpamError, "system command failed");
        return NULL;
    }
    return PyLong_FromLong(sts);
}

static PyMethodDef SpamMethods[] = {
    {"system", spam_system, METH_VARARGS,
     "Execute a shell command."},
    {"divide", spam_divide, METH_VARARGS,
     "Divide two numbers."},
    {NULL, NULL, 0, NULL}};
static struct PyModuleDef spammodule = {
    PyModuleDef_HEAD_INIT,
    "spam",
    NULL,
    -1,
    SpamMethods};
}
