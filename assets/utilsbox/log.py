#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import logging
import platform

__all__ = ["logger"]

if platform.system() == "Windows":
    import ctypes

    ForeGround_White = 0x0007
    ForeGround_Blue = 0x01  # text color contains blue.
    ForeGround_Green = 0x02  # text color contains green.
    ForeGround_Red = 0x04  # text color contains red.
    ForeGround_Yellow = ForeGround_Red | ForeGround_Green
    ForeGround_LowBlue = ForeGround_Blue | ForeGround_Green
    ForeGround_Purple = ForeGround_Red | ForeGround_Blue

    STD_OUTPUT_HANDLE = -11
    std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)


    def set_color(color, handle=std_out_handle):
        bools = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
        return bools

else:
    ForeGround_White = None
    ForeGround_Blue = None
    ForeGround_Green = None
    ForeGround_Red = None
    ForeGround_Yellow = None
    ForeGround_LowBlue = None
    ForeGround_Purple = None


    def set_color(color):
        pass


class LogPublic(object):
    __logger = None

    @staticmethod
    def get_logger(loglevel=logging.INFO, logpath=None, logname="default"):
        if logpath is None or not os.path.isfile(logpath):
            logfolder = os.path.join(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                "logs"
            )
            if not os.path.isdir(logfolder):
                os.makedirs(logfolder)

            createtime = time.strftime('%Y%m%d%H', time.localtime(time.time()))
            logfile = os.path.join(logfolder, "%s.%s.log" % (logname, createtime))

            # format ：设置日志输出格式；
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

            # 创建一个handler，用于写入日志文件：    FileHandler:   输出到文件
            intofile = logging.FileHandler(logfile)
            intofile.setFormatter(formatter)
            # intofile.setLevel(logging.ERROR)    # 生效

            #  创建一个handler，用于输出到控制台：    StreamHandler: 输出到控制台
            console = logging.StreamHandler(sys.stderr)
            console.setFormatter(formatter)
            # console.setLevel(logging.DEBUG)  # 不生效

            # 创建一个自定义logger
            self_logger = logging.getLogger()

            # 给 logger添加 handler ，分别输出到文件和控制台
            self_logger.addHandler(intofile)
            self_logger.addHandler(console)

            # 设置日志的级别。对于低于该级别的日志消息将被忽略。
            self_logger.setLevel(loglevel)

            LogPublic.__logger = self_logger
            return LogPublic

    @staticmethod
    def debug(message):
        LogPublic.__logger.debug(message)

    @staticmethod
    def info(message):
        set_color(ForeGround_LowBlue)
        LogPublic.__logger.info(message)
        set_color(ForeGround_White)

    @staticmethod
    def warn(message):
        set_color(ForeGround_Yellow)
        LogPublic.__logger.warn(message)
        set_color(ForeGround_White)

    @staticmethod
    def error(message):
        set_color(ForeGround_Red)
        LogPublic.__logger.error(message)
        set_color(ForeGround_White)

    @staticmethod
    def critical(message):
        set_color(ForeGround_Purple)
        LogPublic.__logger.critical(message)
        set_color(ForeGround_White)


logger = LogPublic.get_logger(logging.INFO)
# print id(logger)
# logger1 = LogPublic.get_logger()
# print id(logger1)

if __name__ == '__main__':
    logger.debug("debug message")
    logger.info("info message")
    logger.warn("warn message")
    logger.error("error message")
    logger.critical("critical message")
