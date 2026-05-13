# -*- coding: utf-8 -*-
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from Common.Logger import logger
from Common.Vars import project_path

class Email(object):
    def __init__(self):
        self.sender_email = "1099351460@qq.com"  # 发件人
        self.auth_code = "koruroosmsewicbj"  # 授权码
        self.receiver_email = "2840588414@qq.com"  # 收件人

    def send_msg(self, subject, content):
        """发送邮件"""
        msg = MIMEText(content, "plain", "utf-8")
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg['Subject'] = subject

        try:
            server = smtplib.SMTP_SSL("smtp.qq.com", 465)
            server.login(self.sender_email, self.auth_code)
            server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            logger.info("邮件发送成功！")
            server.quit()
        except Exception as e:
            logger.error("发送失败：", e)

    def send_msg_and_file(self, subject, content, file):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg['Subject'] = subject

        msg.attach(MIMEText(content, "plain", "utf-8"))

        with open(file, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        filename = file.split("\\")[-1]
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

        try:
            with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
                server.login(self.sender_email, self.auth_code)
                server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            logger.info("邮件发送成功！")
        except Exception as e:
            logger.error("发送失败：", e)

email = Email()

if __name__ == '__main__':
    subject = "Python 发送的测试邮件"
    content = "这是一封通过 Python 自动发送的 QQ 邮件～"
    file = os.path.join(project_path, 'logs', '2026-03-26.log')
    email.send_msg(subject, content)
    email.send_msg_and_file(subject, content, file)

