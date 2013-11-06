Thoughts
==========

We need a way to determine "routes" and "flows" for messages.  Right now, we
define a "route" to a "page" that allows an upgrade to Web Sockets, but there
is no way to define more complicated protocols.  Is it even necessary to allow
them to be defined?  Right now, we pretty much accept the message, check the
message type, then if we are smart, we dump the message into a method that
processes it.  

It seems like it may be advisable to create a general purpose server (a
framework?  an MVC?  does that even make sense in realtime?) where you define
message types, expected and appropriate responses (maybe the response is
returned from the handler, instead of being transmitted down some file-like
object.)

Maybe we could do something like this::

    #some callables
    from controllers import login_handler, rebroadcast, logout_handler
    
    #you could make these controllers async things...

    message_routes = ( 
        # message type (regex?) -> a controller 
        (r'login', login_handler), 
        (r'broadcast', rebroadcast), 
        (r'logout', logout_handler),
    )

If I were to be inspired by Django, I would possibly use a regex to allow some
more flexibility in terms of message-naming, but I am not convinced that that
flexibility is warrented, or even a good thing.  On the other hand, naming
messages in a heirarchical-seeming manner seems like it could be really
valuable and helpful in terms of system organization::

    message_routes = dict(
        (r'accounts/login', login_handler),
        (r'accounts/logout', logout_handler),
        (r'messages/broadcase', rebroadcast)
    )

Perhaps the messages look like JSON, so like this::

    {'name': 'accounts/login',
     'username': 'kevin',
     'passwordhash': 'abc739d98fsomemd5sum'
    }

Or perhaps, if you want to get 'fancier'::

    { 
        'name': { 
            'accounts' : { 
                'name': 'login'
            }
        },
        'payload': { 
            'username': 'kevin',
            'passwordhash': 'abc123etcetcetc'
        }
    }

Then, inside our Handler, we could do something like this (assuming a Tornadoish app)::
   
    def on_message(self):
        try:
            # where Message is a class that populates "name" and "payload" from our
            # decoded JSON stuff...
            obj = Message(json.loads(message))
            msg_type = message_routes[obj.name](obj.payload)
        except ItDidntWork, er:
            ...     

Now, this covers a pretty simple "request/response" type of scenario, but it
does not address situations where you push data out to lots of clients all at
once.  In a scenario like that, maybe we decorate the controllers?  It seems
there are four scenarios, so four decorator.  A request is sent, and...

    1. A response should be sent to only the sending client.  
    2. A response should be sent to everyone.  
    3. A response should be sent to a subset of clients.  (A null set is a subset)

We could decorate the controllers, so that their return values are either sent
to everyone, the sender, or a subset of clients.  The decorators *could* look like this::

    @silent
    def volume_up(message):
        # do some volume up work.
        return volume

    @send_all
    def broadcast(message):
        # do some work
        return message_to_broadcast
   
    @send_to_mailbox
    def private_message(message, recipient):
        return message_to_send, recipent_list 

I think there is something to be said for any framework being a bit chatty.

The "return to sender" and "broadcast" decorators are easy.  It may be trickier
to make an API that is elegant for responding to a subset of clients.  Does the
sender know who the subset is?  Should it be included in the message?  

If the use-case is something like a "private" message, then the answer is that
the target address should be in the sender's initial message.  There are
systems where messages should go to specific clients, but that the sender is
not aware of the client.  In a case like that, the clients may subscribe to
messages, or there may be a central switchboard who knows to whom messages
should be passed.

It also depends, I suppose, on whether the clients are all similiar or if they
are a heterogenous set of clients that all expect different message types.  If
you are operating a chat-room, all of your clients will be essentially the
same.  If you are an MP3 player, all of your clients may expect very different
kinds of messages... For instance, your mixer may expect "Volume Up" and
"Volume Down" messages, but your decoder only wants messages with the next
frame of the music file.  

It is also possible, actually, probable, that you will want multiple controls
to register against your initial message.  That is, if a "Volume Up" message is
transmitted by a client, you may want to update the client immediately, but
also have the message route to the mixer and to any other graphical client that
is attached.  In a case like that, it may make sense to allow the message to
attach to routes, like so::

     message_routes = dict((
        (r'mixer/volume_up', (increase_volumne, rebroadcast,) ),
        (r'mixer/volumne_down', (decrease_volume, rebroadcast,) ),
        (r'messages/broadcast', (rebroadcast,) )
    ))

These clients could execute in order, though it would probably be better to 
decide in advance that they will execute asyncronously.  That way, we don't
depend on one controller firing before the next.  

