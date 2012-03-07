from djapian import space,Indexer,CompositeIndexer

from data.models import RecipientCountryBudget,Activity,Transaction

#class RecipientCountryBudgetIndexer(Indexer):
    #fields = ['country_name']
    #tags = [
        #('organisation','organisation'),
        #('value','value'),
        #]
#space.add_index(RecipientCountryBudget,RecipientCountryBudgetIndexer,attach_as='indexer')

class ActivityIndexer(Indexer):
    fields = ['title','description','total_budget','organisation']
    tags = [
        ('identifier','identifier'),
        ('organisation','organisation'),
        ('title','title'),
        ('description','description'),
        ('sector','sector'),
        ('sector_code','sector_code'),
        ('pk','pk'),
        ('total_budget','total_budget'),
        ('cntr','recipient_country_code',3),
        #('last_updated','last_updated'),
        ]
space.add_index(Activity,ActivityIndexer,attach_as='indexer')

#class TransactionIndexer(Indexer):
    #fields = ['activity.title']
    #tags = [
        #('transaction_type','transaction_type'),
        #('provider_org','provider_org'),
        #('reciver_org','reciver_org'),
        #('value','value'),
        #('value_date','value_date'),
        #('transaction_date','transaction_date'),
        #]
#space.add_index(Transaction,TransactionIndexer,attach_as='indexer')    


#complete_indexer = CompositeIndexer(RecipientCountryBudget.indexer,Activity.indexer,Transaction.indexer)
complete_indexer = CompositeIndexer(Activity.indexer)