var typeorm = require("typeorm");
var EntitySchema = typeorm.EntitySchema;

const Users = require("./entity/Users")

typeorm.createConnection({
  name: "mysql",
  type: "mysql",
  host: "localhost",
  port: 3306,
  username: process.env.NORTHSTAR_DB_USER,
  password: process.env.NORTHSTAR_DB_PASSWORD,
  database: "northstar_tasks",
  synchronize: true,
  "logging": true,
  entities: [
    new EntitySchema(Users)
  ]
}).then(() => {

  const dbConnection = typeorm.getConnection('mysql')

  const repo = dbConnection.getRepository("Users")
  return repo
}).then((repo) => {


  console.log('Seeding two synthetic local users')
  const inserts = [
    repo.insert({
      name: "Avery",
      address: "Local",
      role: "user"
    }),
    repo.insert({
      name: "Morgan",
      address: "Local",
      role: "admin"
    })
  ];

  return Promise.all(inserts)
}).catch((err) => {
  console.error('failed connecting and seeding users to the MySQL database')
  console.error(err)
})