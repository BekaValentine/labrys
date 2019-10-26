import bcrypt

def get_hashed_password(plain_text_password):
  return bcrypt.hashpw(plain_text_password.encode('utf8'), bcrypt.gensalt(12))

def check_password(plain_text_password, hashed_password):
  return bcrypt.checkpw(plain_text_password.encode('utf8'), hashed_password.encode('utf8'))
