PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE hosts(
    id integer PRIMARY KEY autoincrement,
    sort int default 0,
    name varchar(50) NOT NULL,
    ip varchar(16) NOT NULL,
    user varchar(50) NOT NULL,
    passwd varchar(100),
    port int default 22,
    sudo varchar(50) default "",
    bastion int default 0,
    create_at datetime default (datetime('now', 'localtime')),
    update_at datetime default (datetime('now', 'localtime'))
);
COMMIT;
