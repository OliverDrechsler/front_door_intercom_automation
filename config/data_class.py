#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class Open_Door_Task:
    message_id: int = None
    chat_id: int = None
    open: bool = False
    reply: bool =  False


@dataclass
class Message_Task:
    chat_id: int = None
    message_id: int = None
    data_text: str = None
    filename: str = None
    send: bool = False
    reply: bool  = False
    photo: bool  = False


@dataclass
class Camera_Task:
    chat_id: int = None
    message_id: int = None
    reply: bool = False
    photo: bool = False
    blink_photo: bool = False
    picam_photo: bool = False
    blink_mfa: bool = False
