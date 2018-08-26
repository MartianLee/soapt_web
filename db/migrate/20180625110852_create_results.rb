class CreateResults < ActiveRecord::Migration[5.2]
  def change
    create_table :results do |t|
      t.text :tweet_id
      t.text :tweet_text
      t.integer :sentiment1
      t.integer :sentiment2
      t.integer :sentiment3
      t.integer :sentiment4
      t.integer :sentiment5

      t.timestamps
    end
  end
end
