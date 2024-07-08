#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
import telebot

@dataclass
class Open_Door_Task:
    message: telebot.types.Message = None
    chat_id: int = None
    open: bool = False
    reply: bool =  False


@dataclass
class Message_Task:
    chat_id: int = None
    message: telebot.types.Message = None
    data_text: str = None
    filename: str = None
    send: bool = False
    reply: bool  = False
    photo: bool  = False


@dataclass
class Camera_Task:
    chat_id: int = None
    message: telebot.types.Message = None
    reply: bool = False
    photo: bool = False
    blink_photo: bool = False
    picam_photo: bool = False
    blink_mfa: bool = False
