class CreateUserTweets < ActiveRecord::Migration[5.2]
  def change
    create_table :user_tweets do |t|
      t.text :tweet_id
      t.text :tweet_text

      t.timestamps
    end
  end
end
